import os
import subprocess
import sys
import platform
import urllib.request
import os
from textwrap import dedent
import importlib


required_libraries = ['nbformat'] 
for lib in required_libraries:
    try:
        importlib.import_module(lib)
    except ImportError:
        print(f"Installing {lib}...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', lib])

import nbformat as nbf  # For creating Jupyter notebooks


# Add the directory to sys.path
script_dir = "setup"
if script_dir not in sys.path:
    sys.path.append(script_dir)

from utils import ask_yes_no,is_installed,set_from_env


# Script creation
def create_step_script(language, folder_path, script_name, purpose):
    """
    Creates an individual script (R or Python) with the necessary structure.
    
    Parameters:
    language (str): "r" for R, "python" for Python.
    folder_path (str): The directory where the script will be saved.
    script_name (str): The name of the script (e.g., 'data_collection', 'preprocessing').
    purpose (str): The purpose of the script (e.g., 'Data extraction', 'Data cleaning').
    """
    if language.lower() == "r":
        extension = ".R"
        # Wrap the entire R script content in the raw block
        content = f"""# {% raw %}
# {purpose} code

run_{script_name} <- function() {{
    # {purpose} code
    print('Running {script_name}...')
}}

# If you want to test this script independently, you can call the run() function directly.
if (interactive()) {{
    run_{script_name}()
}}
# {% endraw %}
"""
    elif language.lower() == "python":
        extension = ".py"
        # Wrap the entire Python script content in the raw block
        content = f"""# {% raw %}
# {purpose} code

def run():
    # {purpose} code
    print("Running {script_name}...")

# If you want to test this script independently, you can call the run() function directly.
if __name__ == "__main__":
    run()
# {% endraw %}
"""
    else:
        raise ValueError("Invalid language choice. Please specify 'r' or 'python'.")

    # Define the file path for saving the script
    file_name = f"{script_name}{extension}"
    file_path = os.path.join(folder_path, file_name)

    # Write the script content to the file
    with open(file_path, "w") as file:
        file.write(content)
    print(f"Created: {file_path}")

def create_workflow_script(language, folder_path):
    """
    Creates a workflow script that runs all steps in order.
    
    Parameters:
    language (str): "r" for R, "python" for Python.
    folder_path (str): The directory where the workflow script will be saved.
    """
    if language.lower() == "r":
        extension = ".R"
        # Wrap the entire R workflow script content in the raw block
        content = """
# {% raw %}
# Workflow: Running all steps in order

# Run data collection
source('data_collection.R')

# Run preprocessing
source('preprocessing.R')

# Run modeling
source('modeling.R')

# Run visualization
source('visualization.R')
# {% endraw %}
"""
    elif language.lower() == "python":
        extension = ".py"
        # Wrap the entire Python workflow script content in the raw block
        content = """
# {% raw %}
# Workflow: Running all steps in order

# Load Scripts
import data_collection
import preprocessing
import modeling
import visualization

# Run data collection
data_collection.run()

# Run preprocessing
preprocessing.run()

# Run modeling
modeling.run()

# Run visualization
visualization.run()
# {% endraw %}
"""
    else:
        raise ValueError("Invalid language choice. Please specify 'r' or 'python'.")

    # Define the file path for the workflow script
    workflow_file_name = f"workflow{extension}"
    workflow_file_path = os.path.join(folder_path, workflow_file_name)

    # Write the workflow script content to the file
    with open(workflow_file_path, "w") as file:
        file.write(content)
    print(f"Created: {workflow_file_path}")

def create_project_scripts(language, folder_path):
    """
    Creates a project structure with specific scripts for data science tasks
    and a workflow script in R or Python.
    
    Parameters:
    language (str): "r" for R, "python" for Python.
    folder_path (str): The directory where the scripts will be saved.
    """
    # Ensure the folder exists
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    # Script details based on purpose
    scripts = {
        "data_collection": "Data extraction/scraping",
        "preprocessing": "Data cleaning, transformation, feature engineering",
        "modeling": "Training and evaluation of models",
        "utils": "Helper functions or utilities",
        "visualization": "Functions for plots and visualizations"
    }

    # Create the individual step scripts
    for script_name, purpose in scripts.items():
        create_step_script(language, folder_path, script_name, purpose)

    # Create the workflow script that runs all steps
    create_workflow_script(language, folder_path)


def create_notebooks(language, folder_path, src_folder):
    """
    Creates a notebook (Jupyter for Python, RMarkdown for R) containing the workflow steps
    and loads all scripts from the src_folder in the first cell.
    
    Parameters:
    language (str): "r" for R (RMarkdown), "python" for Python (Jupyter notebook).
    folder_path (str): The directory where the notebook or RMarkdown file will be saved.
    src_folder (str): The directory where the source scripts (e.g., data_collection.R, preprocessing.R) are located.
    """
    # Ensure the notebooks folder exists
    notebooks_folder = os.path.join(folder_path, "notebooks")
    if not os.path.exists(notebooks_folder):
        os.makedirs(notebooks_folder)

    # Define the file name based on the language
    if language.lower() == "python":
        file_name = "workflow_notebook.ipynb"
        file_path = os.path.join(notebooks_folder, file_name)

   
        nb = nbf.v4.new_notebook()

        # First cell: Import all scripts
        cells = [
            nbf.v4.new_markdown_cell("# Workflow: Running all steps in order"),
            nbf.v4.new_markdown_cell("## Loading Scripts"),
            nbf.v4.new_code_cell(f"""
                import sys
                sys.path.append('{src_folder}')
                import data_collection
                import preprocessing
                import modeling
                import visualization
            """),
            nbf.v4.new_markdown_cell("## Run data collection"),
            nbf.v4.new_code_cell("""
                # Run data collection
                data_collection.run()
            """),
            nbf.v4.new_markdown_cell("## Run preprocessing"),
            nbf.v4.new_code_cell("""
                # Run preprocessing
                preprocessing.run()
            """),
            nbf.v4.new_markdown_cell("## Run modeling"),
            nbf.v4.new_code_cell("""
                # Run modeling
                modeling.run()
            """),
            nbf.v4.new_markdown_cell("## Run visualization"),
            nbf.v4.new_code_cell("""
                # Run visualization
                visualization.run()
            """),
        ]
        nb.cells.extend(cells)

        # Write the notebook to a file
        with open(file_path, "w") as f:
            nbf.write(nb, f)
        print(f"Created: {file_path}")

    elif language.lower() == "r":
        file_name = "workflow.Rmd"
        file_path = os.path.join(notebooks_folder, file_name)

        # Create RMarkdown content with the requested structure
        content = dedent(f"""
        ---
        title: "Workflow: Running all steps in order"
        output: html_document
        ---

        # Workflow

        ## Load Scripts
        ```{{r}}
        source('{os.path.join(src_folder, "data_collection.R")}')
        source('{os.path.join(src_folder, "preprocessing.R")}')
        source('{os.path.join(src_folder, "modeling.R")}')
        source('{os.path.join(src_folder, "visualization.R")}')
        ```

        ## Run data collection
        ```{{r}}
        run_data_collection()
        ```

        ## Run preprocessing
        ```{{r}}
        run_preprocessing()
        ```

        ## Run modeling
        ```{{r}}
        run_modeling()
        ```

        ## Run visualization
        ```{{r}}
        run_visualization()
        ```
        """)

        # Write the RMarkdown content to a file
        with open(file_path, "w") as file:
            file.write(content)
        print(f"Created: {file_path}")
    else:
        raise ValueError("Invalid language choice. Please specify 'r' or 'python'.")




# 
def get_hardware_info():
    """
    Extract hardware information and save it to a file.
    Works on Windows, Linux, and macOS.
    """
    os_type = platform.system().lower()
    command = ""

    if os_type == "Windows":
        command = "systeminfo"
    elif os_type == "Linux":
        command = "lshw -short"  # Alternative: "dmidecode"
    elif os_type == "Darwin":  # macOS
        command = "system_profiler SPHardwareDataType"
    else:
        print("Unsupported operating system.")
        return

    try:
        # Execute the command and capture the output
        hardware_info = subprocess.check_output(command, shell=True, text=True)

        # Save the hardware information to a file
        with open("hardware_information.txt", "w") as file:
            file.write(hardware_info)

        print("Hardware information saved to hardware_information.txt")

    except subprocess.CalledProcessError as e:
        print(f"Error retrieving hardware information: {e}")

def setup_virtual_environment(version_control,virtual_environment,repo_platform,repo_name,install_path = "bin/miniconda"):
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
           
        elif version_control == 'Datalad'and not is_installed('rclone', 'Rclone'):    
            install_packages.extend(['rclone'])
 
            if os_type in ["darwin","linux"] and not is_installed('git-annex', 'git-annex'):
                install_packages.extend(['git-annex'])

        if repo_platform == 'GitHub' and not is_installed('gh', 'GitHub Cli'):
             install_packages.extend(['gh'])     
            
        check = setup_conda(install_path,virtual_environment,repo_name, install_packages,env_file)

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

# Conda Setup Functions
def setup_conda(install_path,virtual_environment,repo_name, install_packages = [], env_file = None):
    
    # Set frpm .env file
    set_from_env('conda')

    if not is_installed('conda','Conda'):
        if install_miniconda(install_path):
            if add_miniconda_to_path(install_path):
                if not initialize_conda_shell():
                    return False
            else:
                return False
        else:
            return False
        is_installed('conda','Conda')

    if virtual_environment in ['Python','R']:
        command = ['conda', 'create','--yes', '--name', repo_name, '-c', 'conda-forge']
        command.extend(install_packages)
        msg = f'Conda environment "{repo_name}" for {virtual_environment} created successfully. The following packages were installed: {install_packages}'
    elif virtual_environment in ['environment.yaml','requirements.txt']:
        if virtual_environment == 'requirements.txt':
            generate_yml(repo_name,env_file)
        command = ['conda', 'env', 'create', '-f', env_file, '--name', repo_name]
        msg = f'Conda environment "{repo_name}" created successfully from {virtual_environment}.'
    
    create_conda_env(command,msg)
    export_conda_env(repo_name)
    
    return True
    
def install_miniconda(install_path):
    """
    Downloads and installs Miniconda to a specified location based on the operating system.
    
    Parameters:
    - install_path (str): The absolute path where Miniconda should be installed.

    Returns:
    - bool: True if installation is successful, False otherwise.
    """ 
    os_type = platform.system().lower()
    installer_name = None
    download_dir = os.path.dirname(install_path)  # One level up from the install_path
    installer_path = None
    
    if os_type == "windows":
        installer_name = "Miniconda3-latest-Windows-x86_64.exe"
        url = f"https://repo.anaconda.com/miniconda/{installer_name}"
        installer_path = os.path.join(download_dir, installer_name)
        install_command = [installer_path, "/InstallationType=JustMe", f"/AddToPath=0", f"/RegisterPython=0", f"/S", f"/D={install_path}"]
        
    elif os_type == "darwin":  # macOS
        installer_name = "Miniconda3-latest-MacOSX-arm64.sh" if platform.machine() == "arm64" else "Miniconda3-latest-MacOSX-x86_64.sh"
        url = f"https://repo.anaconda.com/miniconda/{installer_name}"
        installer_path = os.path.join(download_dir, installer_name)
        install_command = ["bash", installer_path, "-b", "-p", install_path]
        
    elif os_type == "linux":
        installer_name = "Miniconda3-latest-Linux-x86_64.sh"
        url = f"https://repo.anaconda.com/miniconda/{installer_name}"
        installer_path = os.path.join(download_dir, installer_name)
        install_command = ["bash", installer_path, "-b", "-p", install_path]
        
    else:
        print("Unsupported operating system.")
        return False
    
    try:
        print(f"Downloading {installer_name} from {url} to {download_dir}...")
        urllib.request.urlretrieve(url, installer_path)
        print("Download complete.")
        
        print("Installing Miniconda...")
        subprocess.run(install_command, check=True)
        if installer_path and os.path.exists(installer_path):
            os.remove(installer_path)
        print("Miniconda installation complete.")
        return True
        
    except Exception as e:
        if installer_path and os.path.exists(installer_path):
            os.remove(installer_path)
        print(f"Failed to install Miniconda: {e}")
        return False

def add_miniconda_to_path(install_path):
    """
    Adds Miniconda's bin (Linux/Mac) or Scripts (Windows) directory to the system PATH.

    Parameters:
    - install_path (str): The absolute path where Miniconda is installed.

    Returns:
    - bool: True if addition to PATH is successful, False otherwise.
    """

    os_type = platform.system().lower()
    conda_bin_path = os.path.join(install_path, 'Scripts' if os_type == 'windows' else 'bin')
    
    try:
        if os_type == 'windows':
            subprocess.run(f'setx PATH "%PATH%;{conda_bin_path}"', shell=True, check=True)
            print("Miniconda path added to system PATH (permanent for Windows).")
        else:
            shell_profile = os.path.expanduser("~/.bashrc" if os_type == "linux" else "~/.zshrc")
            with open(shell_profile, "a") as file:
                file.write(f'\n# Miniconda path\nexport PATH="{conda_bin_path}:$PATH"\n')
            os.environ["PATH"] = f"{conda_bin_path}:{os.environ['PATH']}"
            print(f"Miniconda path added to PATH. Please restart your terminal or source your {shell_profile} to apply.")
        return True
        
    except Exception as e:
        print(f"Failed to add Miniconda to PATH: {e}")
        return False

def initialize_conda_shell():
    """
    Initializes Conda for the user's shell by running `conda init` and starting a new interactive shell session.

    Returns:
    - bool: True if Conda shell initialization is successful, False otherwise.
    """
    try:
        subprocess.run(["conda", "init"], check=True)
        print("Conda shell initialization complete.")
        return True

    except Exception as e:
        print(f"Failed to initialize Conda shell: {e}")
        return False

def create_conda_env(command,msg):
    """
    Create a conda environment from an environment.yml file with a specified name.
    
    Parameters:
    - env_file: str, path to the environment YAML file. Defaults to 'environment.yml'.
    - env_name: str, optional name for the new environment. If provided, overrides the name in the YAML file.
    """
    try:

        # Run the command
        subprocess.run(command, check=True)
        print(msg)
        
    except subprocess.CalledProcessError as e:
        print(f"Failed to create conda environment: {e}")
    except FileNotFoundError:
        print("Conda is not installed or not found in the system path.")
    except Exception as e:
        print(f"An error occurred: {e}")

def generate_yml(env_name,requirements_path):
    """Generate an environment.yml file using a requirements.txt file."""
    yml_content = f"""
        name: {env_name}
        channels:
        - conda-forge
        dependencies:
        - python>=3.5
        - anaconda
        - pip
        - pip:
            - -r file:{requirements_path}
        """
    with open('environment.yml', 'w') as yml_file:
        yml_file.write(yml_content)
    print(f"Generated environment.yml file using {requirements_path}.")

def export_conda_env(env_name, output_file='environment.yml'):
    """
    Export the details of a conda environment to a YAML file.
    
    Parameters:
    - env_name: str, name of the conda environment to export.
    - output_file: str, name of the output YAML file. Defaults to 'environment.yml'.
    """
    try:
        # Use subprocess to run the conda export command
        with open(output_file, 'w') as f:
            subprocess.run(['conda', 'env', 'export', '-n', env_name], stdout=f, check=True)
        
        print(f"Conda environment '{env_name}' exported to {output_file}.")

    except subprocess.CalledProcessError as e:
        print(f"Failed to export conda environment: {e}")
    except FileNotFoundError:
        print("Conda is not installed or not found in the system path.")
    except Exception as e:
        print(f"An error occurred: {e}")

setup_version_control = "setup/version_control.py"
setup_remote_repository = "setup/remote_repository.py"
setup_bash_script = "setup/create.sh"
setup_powershell_script = "setup/create.ps1"

miniconda_path =  "bin/miniconda"

virtual_environment = "{{ cookiecutter.virtual_environment}}"
repo_name = "{{ cookiecutter.repo_name }}"
repo_platform = "{{ cookiecutter.repository_platform}}"
version_control = "{{cookiecutter.version_control}}"
remote_storage = "{{cookiecutter.remote_storage}}"


# Create scripts and nptebooks
create_project_scripts(virtual_environment,"src")
create_notebooks(virtual_environment, "notebooks","src")

# Create Virtual Environment
repo_name = setup_virtual_environment(version_control,virtual_environment,repo_platform,repo_name,miniconda_path)

os_type = platform.system().lower()

if os_type == "windows":
    run_powershell_script(setup_powershell_script, repo_name, setup_version_control, setup_remote_repository)
elif os_type == "darwin" or os_type == "linux":
    run_bash_script(setup_bash_script, repo_name, setup_version_control, setup_remote_repository)



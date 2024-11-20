import os
import subprocess
import sys
import platform
from textwrap import dedent
import importlib
import shutil

required_libraries = ['python-dotenv','nbformat'] 
for lib in required_libraries:
    try:
        importlib.import_module(lib)
    except ImportError:
        print(f"Installing {lib}...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', lib])

import nbformat as nbf  # For creating Jupyter notebooks

from dotenv import load_dotenv

def ask_yes_no(question):
    """
    Prompt the user with a yes/no question and validate the input.

    Args:
        question (str): The question to display to the user.

    Returns:
        bool: True if the user confirms (yes/y), False if the user declines (no/n).
    """
    while True:
        response = input(question).strip().lower()
        if response in {"yes", "y"}:
            return True
        elif response in {"no", "n"}:
            return False
        else:
            print("Invalid response. Please answer with 'yes' or 'no'.")

def load_from_env(env_var: str, env_file=".env"):
    # Load the .env file
    load_dotenv(env_file)

    # Get the environment variable for the executable (uppercase)
    return os.getenv(env_var.upper())

def set_from_env(executable: str, env_file=".env"):
    """
    Tries to load the environment variable for the given executable from the .env file.
    If the variable exists and points to a valid binary path, adds it to the system PATH.

    Args:
        executable (str): The name of the executable.
        env_file (str): The path to the .env file. Defaults to '.env'.
    """
    env_var = load_from_env(executable, env_file)
    if not env_var:
        return False

    # Construct the binary path
    if os.path.exists(env_var):    
        if add_to_path(executable, os.path.dirname(env_var)):
            if shutil.which(executable):
                print(f"{executable.upper()} from .env file has been set to path: {shutil.which(executable)})")
                return True
    return False

def add_to_path(executable: str = None,bin_path: str = None):
        """
        Adds the path of an executalbe binary to the system PATH permanently.
        """
        os_type = platform.system().lower() 
        if os.path.exists(bin_path):
                    # Add to current session PATH
            os.environ["PATH"] += os.pathsep + bin_path

            if os_type == "windows":
                # Use setx to set the environment variable permanently in Windows
                subprocess.run(["setx", "PATH", f"{bin_path};%PATH%"], check=True)
                return True
            else:
                # On macOS/Linux, you can add the path to the shell profile file
                profile_file = os.path.expanduser("~/.bashrc")  # or ~/.zshrc depending on shell
                with open(profile_file, "a") as file:
                    file.write(f'\nexport PATH="{bin_path}:$PATH"')
                print(f"Added {bin_path} to PATH. Restart the terminal or source {profile_file} to apply.")
                return True
        else:
            print(f"{executable} binary not found in {bin_path}, unable to add to PATH.")
            return False
        
def add_to_env(executable: str = None,env_file=".env"):
    # Check if .env file exists
    if not os.path.exists(env_file):
        print(f"{env_file} does not exist. Creating a new one.")
    
    # Write the credentials to the .env file
    with open(env_file, 'a') as file:  
        file.write(f"{executable.upper()}={shutil.which(executable)}\n")

def is_installed(executable: str = None, name: str = None):
    # Check if both executable and name are provided as strings
    if not isinstance(executable, str) or not isinstance(name, str):
        raise ValueError("Both 'executable' and 'name' must be strings.")
    if not set_from_env(executable):
        # Check if the executable is on the PATH
        path = shutil.which(executable)
        if path:
            add_to_env(executable)
            return True
        else: 
            print(f"{name} is not on Path")
            return False
  

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

def create_scripts(language, folder_path):
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

def create_notebooks(language, folder_path):
    """
    Creates a notebook (Jupyter for Python, RMarkdown for R) containing the workflow steps
    and loads all scripts from the src_folder in the first cell.
    
    Parameters:
    language (str): "r" for R (RMarkdown), "python" for Python (Jupyter notebook).
    folder_path (str): The directory where the notebook or RMarkdown file will be saved.
    src_folder (str): The directory where the source scripts (e.g., data_collection.R, preprocessing.R) are located.
    """
    # Ensure the notebooks folder exists
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    # Define the file name based on the language
    if language.lower() == "python":
        file_name = "workflow_notebook.ipynb"
        file_path = os.path.join(folder_path, file_name)

   
        nb = nbf.v4.new_notebook()

        # First cell: Import all scripts
        cells = [
            nbf.v4.new_markdown_cell("# Workflow: Running all steps in order"),
            nbf.v4.new_markdown_cell("### Loading Scripts"),
            nbf.v4.new_code_cell(
                "import sys\n"
                "sys.path.append('src')\n"
                "import data_collection\n"
                "import preprocessing\n"
                "import modeling\n"
                "import visualization\n"
            ),
            nbf.v4.new_markdown_cell("### Run data collection"),
            nbf.v4.new_code_cell("""data_collection.run()"""),
            nbf.v4.new_markdown_cell("### Run preprocessing"),
            nbf.v4.new_code_cell("""preprocessing.run()"""),
            nbf.v4.new_markdown_cell("### Run modeling"),
            nbf.v4.new_code_cell("""modeling.run()"""),
            nbf.v4.new_markdown_cell("### Run visualization"),
            nbf.v4.new_code_cell("""visualization.run()""")
        ]
        nb.cells.extend(cells)

        # Write the notebook to a file
        with open(file_path, "w") as f:
            nbf.write(nb, f)
        print(f"Created: {file_path}")

    elif language.lower() == "r":
        file_name = "workflow.Rmd"
        file_path = os.path.join(folder_path, file_name)

        # Create RMarkdown content with the requested structure
        content = dedent("""{% raw %}
        ---
        title: "Workflow: Running all steps in order"
        output: html_document
        ---

        # Workflow

        ## Load Scripts
        ```{r}             
        source("/src/data_collection.R")
        source("/src/preprocessing.R")
        source("/src/modeling.R")
        source("/src/visualization.R")
        ```
        ## Run data collection
        ```{r}
        run_data_collection()
        ```
        ## Run preprocessing
        ```{r}
        run_preprocessing()
        ```
        ## Run modeling
        ```{r}
        run_modeling()
        ```
        ## Run visualization
        ```{r}
        run_visualization()
        ```
        {% endraw %}""")

        # Write the RMarkdown content to a file
        with open(file_path, "w") as file:
            file.write(content)
        print(f"Created: {file_path}")
    else:
        raise ValueError("Invalid language choice. Please specify 'r' or 'python'.")

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




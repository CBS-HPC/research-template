import os
import subprocess
import sys
import platform
from textwrap import dedent
import importlib
import shutil
import json
import re


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
  

# Scripts and README creation
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

def generate_readme(project_name, project_description,setup,usage,contact,readme_file = None):
    """
    Generates a README.md file with the project structure (from a tree command),
    project name, and description.

    Parameters:
    - project_name (str): The name of the project.
    - project_description (str): A short description of the project.
    """
 
    # Project header
    header = f"""{project_name}
==============================
{project_description}

Setup and Installation
------------
{setup}

Usage
------------
{usage}

Contact Information
------------
{contact}

Project Tree
------------

------------
"""

    # Write the README.md content
    if readme_file is None:
        readme_file = "README.md"
    with open(readme_file, "w",encoding="utf-8") as file:
        file.write(header)
    print(f"README.md created at: {readme_file}")

def create_tree(readme_file=None, ignore_list=None, file_descriptions=None, root_folder=None):
    """
    Updates the "Project Tree" section in a README.md file with the project structure.

    Parameters:
    - readme_file (str): The README file to update. Defaults to "README.md".
    - ignore_list (list): Files or directories to ignore.
    - file_descriptions (dict): Descriptions for files and directories.
    - root_folder (str): The root folder to generate the tree structure from. Defaults to the current working directory.
    """
    def generate_tree(folder_path, prefix=""):
        """
        Recursively generates a tree structure of the folder.

        Parameters:
        - folder_path (str): The root folder path.
        - prefix (str): The prefix for the current level of the tree.
        """
        tree = []
        items = sorted(os.listdir(folder_path))  # Sort items for consistent structure
        for index, item in enumerate(items):
            if item in ignore_list:
                continue
            item_path = os.path.join(folder_path, item)
            is_last = index == len(items) - 1
            tree_symbol = "└── " if is_last else "├── "
            description = f" <- {file_descriptions.get(item, '')}" if file_descriptions and item in file_descriptions else ""
            tree.append(f"{prefix}{tree_symbol}{item}{description}  ") # Add spaces for a line break
            if os.path.isdir(item_path):
                child_prefix = f"{prefix}    " if is_last else f"{prefix}│   "
                tree.extend(generate_tree(item_path, prefix=child_prefix))
        return tree

    if not readme_file:
        readme_file = "README.md"

    if not os.path.exists(readme_file):
        print(f"README file '{readme_file}' does not exist. Exiting.")
        return

    if ignore_list is None:
        ignore_list = []  # Default to an empty list if not provided


    if isinstance(file_descriptions, str) and file_descriptions.endswith(".json") and os.path.exists(file_descriptions): 
        with open(file_descriptions, "r", encoding="utf-8") as json_file:
            file_descriptions = json.load(json_file)
    else:
        file_descriptions = None

    if not root_folder:
        root_folder = os.getcwd()

    # Read the existing README.md content
    with open(readme_file, "r", encoding="utf-8") as file:
        readme_content = file.readlines()

    # Check for "Project Tree" section
    start_index = None
    for i, line in enumerate(readme_content):
        if line.strip() == "Project Tree" and i + 1 < len(readme_content) and readme_content[i + 1].strip() == "------------":
            start_index = i + 2  # The line after "------------"
            break

    if start_index is None:
        print("No 'Project Tree' section found in the README. No changes made.")
        return

    # Find the end of the "Project Tree" section
    end_index = start_index
    while end_index < len(readme_content) and readme_content[end_index].strip() != "------------":
        end_index += 1

    if end_index >= len(readme_content):
        print("No closing line ('------------') found for 'Project Tree'. No changes made.")
        return

    # Generate the folder tree structure
    tree_structure = generate_tree(root_folder)

    # Replace the old tree structure in the README
    updated_content = (
        readme_content[:start_index] +  # Everything before the tree
        [line + "\n" for line in tree_structure] +  # The new tree structure
        readme_content[end_index:]  # Everything after the closing line
    )

    # Write the updated README.md content
    with open(readme_file, "w", encoding="utf-8") as file:
        file.writelines(updated_content)

    print(f"'Project Tree' section updated in '{readme_file}'.")

def create_tree_old(readme_file = None, ignore_list=None ,file_descriptions = None,root_folder = None):
    """
    README.md file with the project structure (from a tree command),

    """
    def generate_tree(folder_path, prefix=""):
        """
        Recursively generates a tree structure of the folder.

        Parameters:
        - folder_path (str): The root folder path.
        - prefix (str): The prefix for the current level of the tree.
        """
        tree = []
        items = sorted(os.listdir(folder_path))  # Sort items for consistent structure
        for index, item in enumerate(items):
            if item in ignore_list:
                continue
            item_path = os.path.join(folder_path, item)
            is_last = index == len(items) - 1
            tree_symbol = "└── " if is_last else "├── "
            description = f" <- {file_descriptions.get(item, '')}" if item in file_descriptions else ""
            tree.append(f"{prefix}{tree_symbol}{item}{description}  ") # Add spaces for a line break
            if os.path.isdir(item_path):
                child_prefix = f"{prefix}    " if is_last else f"{prefix}│   "
                tree.extend(generate_tree(item_path, prefix=child_prefix))
        return tree

     # Write the README.md content
    
    if not readme_file:
        readme_file = "README.md"
    
    if not os.path.exists(readme_file):
        return 

    if ignore_list is None:
        ignore_list = []  # Default to an empty list if not provided

    if file_descriptions is None:
        # Define file and folder descriptions
        file_descriptions = {
            "Makefile": "Makefile with commands like `make data` or `make train`",
            "README.md": "The top-level README for developers using this project.",
            "data": "Directory for datasets.",
            "external": "Data from third-party sources.",
            "interim": "Intermediate data transformed during the workflow.",
            "processed": "The final, clean data used for analysis or modeling.",
            "raw": "Original, immutable raw data.",
            "docs": "Documentation files.",
            "models": "Trained models and their outputs.",
            "notebooks": "Jupyter or R notebooks for exploratory and explanatory work.",
            "references": "Manuals, data dictionaries, or other resources.",
            "reports": "Generated reports, including figures.",
            "figures": "Generated graphics and figures to be used in reporting.",
            "requirements.txt": "The requirements file for reproducing the analysis environment.",
            "setup.py": "Makes project pip installable (pip install -e .) so `src` can be imported.",
            "src": "Source code for use in this project.",
            "__init__.py": "Makes `src` a Python module.",
            "data": "Scripts to download or generate data.",
            "make_dataset.py": "Script to create datasets.",
            "features": "Scripts to turn raw data into features for modeling.",
            "build_features.py": "Script to build features for modeling.",
            "predict_model.py": "Script to make predictions using trained models."
        }
        # Save to JSON file
        with open("setup/file_descriptions.json", "w", encoding="utf-8") as json_file:
            json.dump(file_descriptions, json_file, indent=4, ensure_ascii=False)
    elif isinstance(file_descriptions, str) and file_descriptions.endswith(".json") and os.path.exists(file_descriptions): 
            with open(file_descriptions, "r", encoding="utf-8") as json_file:
                file_descriptions = json.load(json_file)

    # Generate the folder tree structure
    if not root_folder: 
        root_folder = os.getcwd()
    tree_structure = generate_tree(root_folder)
 
    with open(readme_file, "w",encoding="utf-8") as file:
        file.write("\n".join(tree_structure))

def update_file_descriptions(readme_path, json_file="setup/file_descriptions.json"):
    """
    Reads the project tree from an existing README.md and updates a file_descriptions.json file.

    Parameters:
    - readme_path (str): Path to the README.md file.
    - setup_folder (str): Path to the setup folder where file_descriptions.json will be saved.
    - json_file (str): The name of the JSON file for file descriptions.

    Returns:
    - None
    """
    if not os.path.exists(readme_path):
        return 
 
    # Read existing descriptions if the JSON file exists
    if os.path.exists(json_file):
        with open(json_file, "r", encoding="utf-8") as f:
            file_descriptions = json.load(f)
    else:
        file_descriptions = {
            "Makefile": "Makefile with commands like `make data` or `make train`",
            "README.md": "The top-level README for developers using this project.",
            "data": "Directory for datasets.",
            "external": "Data from third-party sources.",
            "interim": "Intermediate data transformed during the workflow.",
            "processed": "The final, clean data used for analysis or modeling.",
            "raw": "Original, immutable raw data.",
            "docs": "Documentation files.",
            "models": "Trained models and their outputs.",
            "notebooks": "Jupyter or R notebooks for exploratory and explanatory work.",
            "references": "Manuals, data dictionaries, or other resources.",
            "reports": "Generated reports, including figures.",
            "figures": "Generated graphics and figures to be used in reporting.",
            "requirements.txt": "The requirements file for reproducing the analysis environment.",
            "setup.py": "Makes project pip installable (pip install -e .) so `src` can be imported.",
            "src": "Source code for use in this project.",
            "__init__.py": "Makes `src` a Python module.",
            "data": "Scripts to download or generate data.",
            "make_dataset.py": "Script to create datasets.",
            "features": "Scripts to turn raw data into features for modeling.",
            "build_features.py": "Script to build features for modeling.",
            "predict_model.py": "Script to make predictions using trained models."
        }
        # Save to JSON file
        with open(json_file, "w", encoding="utf-8") as json_file:
            json.dump(file_descriptions, json_file, indent=4, ensure_ascii=False)

    # Read the README.md and extract the "Project Tree" section
    with open(readme_path, "r", encoding="utf-8") as f:
        readme_content = f.read()

    # Extract the project tree section using regex
    tree_match = re.search(r"Project Tree\s*[-=]+\s*\n([\s\S]+)", readme_content)
    if not tree_match:
        raise ValueError("Project Tree section not found in README.md")

    project_tree = tree_match.group(1)

    # Extract file descriptions from the project tree
    tree_lines = project_tree.splitlines()
    for line in tree_lines:
        while line.startswith("│   "):
            line = line[4:]  # Remove prefix (4 characters)
        match = re.match(r"^\s*(├──|└──|\|.*)?\s*(\S+)\s*(<- .+)?$", line)
        if match:
            filename = match.group(2).strip()
            description = match.group(3)  # This captures everything after '<-'
            if description:
                description = description.strip()[3:]  # Remove the '<- ' part and get the description text
            if description:
                file_descriptions[filename] = description

    # Write the updated descriptions to the JSON file
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(file_descriptions, f, indent=4, ensure_ascii=False)

    print(f"File descriptions updated in {json_file}")

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




import os
import subprocess
import sys
import platform
from textwrap import dedent
import importlib
import shutil
import json
import re
import zipfile
import urllib.request

required_libraries = ['python-dotenv','rpds-py==0.21.0','nbformat','requests'] 
for lib in required_libraries:
    try:
        importlib.import_module(lib)
    except ImportError:
        print(f"Installing {lib}...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', lib])

import nbformat as nbf  # For creating Jupyter notebooks
from dotenv import load_dotenv
import requests


def get_relative_path(target_path):

    if target_path:
        current_dir = os.getcwd()
        absolute_target_path = os.path.abspath(target_path)
        
        # Check if target_path is a subpath of current_dir
        if os.path.commonpath([current_dir, absolute_target_path]) == current_dir:
            # Create a relative path if it is a subpath
            relative_path = os.path.relpath(absolute_target_path, current_dir)

        if relative_path:
            return relative_path

    return target_path

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
    load_dotenv(env_file,override=True)

    # Get the environment variable for the executable (uppercase)
    return os.getenv(env_var.upper())

def save_to_env(env_var: str, env_name: str, env_file=".env"):
    """
    Saves or updates an environment variable in a .env file (case-insensitive for variable names).
    
    Args:
        env_var (str): The value of the environment variable to save.
        env_name (str): The name of the environment variable (case-insensitive).
        env_file (str): The path to the .env file. Defaults to ".env".
    """
    if env_var is None:
        return
    # Standardize the variable name for comparison
    env_name_upper = env_name.strip().upper()
    
    # Read the existing .env file if it exists
    env_lines = []
    if os.path.exists(env_file):
        with open(env_file, 'r') as file:
            env_lines = file.readlines()

    # Check if the variable exists (case-insensitive) and update it
    variable_exists = False
    for i, line in enumerate(env_lines):
        # Split each line to isolate the variable name
        if "=" in line:
            existing_name, _ = line.split("=", 1)
            if existing_name.strip().upper() == env_name_upper:
                env_lines[i] = f"{env_name_upper}={env_var}\n"  # Preserve original case in name
                variable_exists = True
                break

    # If the variable does not exist, append it
    if not variable_exists:
        env_lines.append(f"{env_name_upper}={env_var}\n")
    
    # Write the updated lines back to the file
    with open(env_file, 'w') as file:
        file.writelines(env_lines)

def exe_to_path(executable: str = None, path: str = None):
    """
    Adds the path of an executable binary to the system PATH permanently.
    """
    os_type = platform.system().lower()
    
    if not executable or not path:
        print("Executable and path must be provided.")
        return False

    if os.path.exists(path):
        # Add to current session PATH
        os.environ["PATH"] += os.pathsep + path

        if os_type == "windows":
            # Use setx to set the environment variable permanently in Windows
            subprocess.run(["setx", "PATH", f"{path};%PATH%"], check=True)
        else:
            # On macOS/Linux, add the path to the shell profile file
            profile_file = os.path.expanduser("~/.bashrc")  # or ~/.zshrc depending on the shell
            with open(profile_file, "a") as file:
                file.write(f'\nexport PATH="{path}:$PATH"')

        # Check if executable is found in the specified path
        resolved_path = shutil.which(executable)
        if resolved_path and os.path.dirname(resolved_path) == path:
            print(f"{executable} binary is added to PATH and resolved correctly_dre: {path}")
            return True
        elif resolved_path:
            print(f"{executable} binary available at a wrong path_dre: {resolved_path}")
            return True
        else:
            print(f"{executable} binary is not found in the specified PATH_dre: {path}")
            return False
    else:
        print(f"Path does not exist_dre: {path}")
        return False



def path_from_env(path: str):
    """
    Removes a specific path from the system PATH for the current session and permanently if applicable.
    
    Args:
        path (str): The path to remove from the PATH environment variable.

    Returns:
        bool: True if the path was successfully removed, False otherwise.
    """
    if not path:
        print("No path provided to remove.")
        return False

    # Normalize the path for comparison
    path = os.path.normpath(path)
    
    # Split the current PATH into a list
    current_paths = os.environ["PATH"].split(os.pathsep)
    
    if path not in map(os.path.normpath, current_paths):
        print(f"Path {path} is not in the current PATH.")
        return False

    # Remove the specified path
    filtered_paths = [p for p in current_paths if os.path.normpath(p) != path]
    os.environ["PATH"] = os.pathsep.join(filtered_paths)

    # Update PATH permanently
    os_type = platform.system().lower()
    if os_type == "windows":
        # Use setx to update PATH permanently on Windows
        try:
            subprocess.run(["setx", "PATH", os.environ["PATH"]], check=True)
            print(f"Path {path} removed permanently on Windows.")
        except subprocess.CalledProcessError as e:
            print(f"Failed to update PATH permanently on Windows: {e}")
            return False
    else:
        # On macOS/Linux, remove the path from the shell profile file
        profile_file = os.path.expanduser("~/.bashrc")  # or ~/.zshrc depending on the shell
        if os.path.exists(profile_file):
            try:
                with open(profile_file, "r") as file:
                    lines = file.readlines()
                with open(profile_file, "w") as file:
                    for line in lines:
                        if f'export PATH="{path}:$PATH"' not in line.strip():
                            file.write(line)
                print(f"Path {path} removed permanently in {profile_file}.")
            except Exception as e:
                print(f"Failed to update {profile_file}: {e}")
                return False

    print(f"Path {path} removed successfully.")
    return True



def exe_to_env(executable: str = None, path: str = None, env_file: str = ".env"):
    """
    Adds the path of an executable binary to an environment file.
    """
    if not executable:
        print("Executable must be provided.")
        return False

    # Attempt to resolve path if not provided
    if not path or not os.path.exists(path):
        path = os.path.dirname(shutil.which(executable))
    
    if path:
        # Save to environment file
        save_to_env(path, executable.upper())  # Assuming `save_to_env` is defined elsewhere
        load_dotenv(env_file, override=True)  # Reload the .env file

        # Check if executable is found in the specified path
        resolved_path = shutil.which(executable)
        if resolved_path and os.path.dirname(resolved_path) == path:
            print(f"{executable} binary is added to the environment and resolved correctly: {path}")
            return True
        elif resolved_path:
            print(f"{executable} binary available at a wrong path: {resolved_path}")
            return True
        else:
            print(f"{executable} binary is not found in the specified environment PATH: {path}")
            return False
    else:
        print(f"Path does not exist_dre2: {path}")
        return False

def is_installed(executable: str = None, name: str = None,env_file:str = ".env"):
    
    if name is None:
        name = executable

    # Check if both executable and name are provided as strings
    if not isinstance(executable, str) or not isinstance(name, str):
        raise ValueError("Both 'executable' and 'name' must be strings.")
    
    path = load_from_env(executable)

    if path and os.path.exists(path):
        return exe_to_path(executable, path)
    
    elif path and not os.path.exists(path):
        path_from_env(path)
    
    if not path and shutil.which(executable):
        exe_to_env(executable)
    else:
        print(f"{name} is not on Path")
        return False

# Scripts creation
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


# README
def creating_readme(repo_name ,project_name, project_description,repo_platform,author_name):

    if repo_platform.lower() in ["github","gitlab"]:
        web_repo = repo_platform.lower()
        setup = f"""git clone https://{web_repo}.com/username/{repo_name}.git"" \
        cd {repo_name} \
        python setup.py"""
    else: 
        setup = f"""cd {repo_name} python setup.py"""
    usage = """python src/workflow.py"""
    contact = f"{author_name}"

    # Create and update README and Project Tree:
    update_file_descriptions("README.md", json_file="setup/file_descriptions.json")
    generate_readme(project_name, project_description,setup,usage,contact,"README.md")
    create_tree("README.md", ['.git','.datalad','.gitkeep','.env','__pycache__'] ,"setup/file_descriptions.json")
    
def generate_readme(project_name, project_description,setup,usage,contact,readme_file = None):
    """
    Generates a README.md file with the project structure (from a tree command),
    project name, and description.

    Parameters:
    - project_name (str): The name of the project.
    - project_description (str): A short description of the project.
    """


    # Project header
    header = f"""# {project_name}


{project_description}

## Installation
```
{setup}
```
## Usage
```
{usage}
```
## Contact Information
{contact}

## Project Tree
------------

------------
"""
    if readme_file is None:
        readme_file = "README.md" 
    if os.path.exists(readme_file):
        return
    
    # Write the README.md content
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
        tree.append('<span style="font-size: 9px;">')
        items = sorted(os.listdir(folder_path))  # Sort items for consistent structure
        for index, item in enumerate(items):
            if item in ignore_list:
                continue
            item_path = os.path.join(folder_path, item)
            is_last = index == len(items) - 1
            tree_symbol = "└── " if is_last else "├── "
            description = f" <- {file_descriptions.get(item, '')}" if file_descriptions and item in file_descriptions else ""
            tree.append(f"{prefix}{tree_symbol}{item}{description}<br> ") # Add spaces for a line break
            if os.path.isdir(item_path):
                child_prefix = f"{prefix}    " if is_last else f"{prefix}│   "
                tree.extend(generate_tree(item_path, prefix=child_prefix))
        
        tree.append("</span>")
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
        if "Project Tree" in line.strip() and i + 1 < len(readme_content) and readme_content[i + 1].strip() == "------------":
        #if line.strip() == "Project Tree" and i + 1 < len(readme_content) and readme_content[i + 1].strip() == "------------":
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
        with open(json_file, "w", encoding="utf-8") as file:
            json.dump(file_descriptions, file, indent=4, ensure_ascii=False)

    if not os.path.exists(readme_path):
        return 

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


def set_from_env():
  
    is_installed('git')
    is_installed('datalad')
    is_installed('git-annex')
    is_installed('rclone')


# Git Functions:
def git_commit(msg:str=""):
    
    # Set from .env file
    is_installed('git')

    try:
        subprocess.run(["git", "add", "."], check=True)    
        subprocess.run(["git", "commit", "-m", msg], check=True)
    except subprocess.CalledProcessError as e:
        print(f"An error occurred: {e}")

def git_push(msg:str=""):

    def push_all(remote="origin"):
        try:
            # Get the name of the current branch
            current_branch = subprocess.check_output(
                ["git", "branch", "--show-current"],
                text=True
            ).strip()
            
            # Get all local branches
            branches = subprocess.check_output(
                ["git", "branch"],
                text=True
            ).strip().splitlines()
            
            # Clean up branch names
            branches = [branch.strip().replace("* ", "") for branch in branches]
            
            # Filter out the current branch
            branches_to_push = [branch for branch in branches if branch != current_branch]
            
            # Push each branch except the current one
            for branch in branches_to_push:
                subprocess.run(
                    ["git", "push", remote, branch],
                    check=True
                )
            
            print(f"Successfully pushed all branches except '{current_branch}'")
        except subprocess.CalledProcessError as e:
            print(f"Error occurred while pushing branches: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")

    try:
        if os.path.isdir(".datalad"):
            # Set from .env file
            is_installed('git')
            is_installed('datalad')
            is_installed('git-annex')
            is_installed('rclone')
            subprocess.run(["datalad", "save", "-m", msg], check=True)
            push_all()

        elif os.path.isdir(".git"):
            git_commit(msg)
            result = subprocess.run(["git", "branch", "--show-current"], check=True, capture_output=True, text=True)
            branch = result.stdout.strip()  # Remove any extra whitespace or newlin
            if branch:
                subprocess.run(["git", "push", "origin", branch], check=True)
            else:
                subprocess.run(["git", "push", "--all"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"An error occurred: {e}")

def git_user_info():
        git_name = None
        git_email = None
        while not git_name or not git_email:
            git_name = input("Enter your Git user name: ").strip()
            git_email = input("Enter your Git user email: ").strip()
            # Check if inputs are valid
            if not git_name or not git_email:
                print("Both name and email are required.")
        save_to_env(git_name ,'GIT_USER')
        save_to_env(git_email,'GIT_EMAIL')
        return git_name, git_email

def git_repo_user(repo_name,repo_platform):
    if repo_platform in ["GitHub","GitLab"]: 
        repo_user = None 
        privacy_setting = None
        while not repo_user or not privacy_setting:
            repo_user = input(f"Enter your {repo_platform} username:").strip()
            privacy_setting = input("Select the repository visibility (private/public): ").strip().lower()

            if privacy_setting not in ["private", "public"]:
                print("Invalid choice. Defaulting to 'private'.")
                privacy_setting = None

        save_to_env(repo_user,f"{repo_platform}_USER")
        save_to_env(privacy_setting,f"{repo_platform}_PRIVACY")
        save_to_env(repo_name,f"{repo_platform}_REPO") 
        
        return repo_user, privacy_setting
    else:
        return None, None


# Conda Functions:
def setup_conda(install_path,virtual_environment,repo_name, install_packages = [], env_file = None):
    
    install_path = os.path.abspath(install_path)

    if not is_installed('conda','Conda'):
        if not install_miniconda(install_path):
            return False

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

def init_conda():
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

def install_miniconda(install_path):
    """
    Downloads and installs Miniconda3 to a specified location based on the operating system.
    
    Parameters:
    - install_path (str): The absolute path where Miniconda3 should be installed.

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
        install_command = ["bash", installer_path, "-b","-f","-p", install_path]
        
    elif os_type == "linux":
        installer_name = "Miniconda3-latest-Linux-x86_64.sh"
        url = f"https://repo.anaconda.com/miniconda/{installer_name}"
        installer_path = os.path.join(download_dir, installer_name)
        install_command = ["bash", installer_path, "-b","-f","-p", install_path]
        
    else:
        print("Unsupported operating system.")
        return False
    
    try:
        print(f"Downloading {installer_name} from {url} to {download_dir}...")
        urllib.request.urlretrieve(url, installer_path)
        print("Download complete.")
        
        print("Installing Miniconda3...")
        subprocess.run(install_command, check=True)
        if installer_path and os.path.exists(installer_path):
            os.remove(installer_path)
        
        #if exe_to_env("conda",os.path.join(install_path,"bin")):
        if exe_to_path("conda",os.path.join(install_path, "bin")): 
            if not init_conda():
                return False
        else:
            return False
        
        if is_installed('conda','Conda'):
            print("Miniconda3 installation complete.")
            return True
        else:
            return False
    
    except Exception as e:
        if installer_path and os.path.exists(installer_path):
            os.remove(installer_path)
        print(f"Failed to install Miniconda3: {e}")
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


# Other
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


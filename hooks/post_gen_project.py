import os
import subprocess
import sys
import os

# Add the directory to sys.path
script_dir = "setup"
if script_dir not in sys.path:
    sys.path.append(script_dir)

def create_steps(language, folder_path, script_name, purpose):
    """
    Creates an individual script (R or Python) with the necessary structure.

    Parameters:
    language (str): "r" for R, "python" for Python.
    folder_path (str): The directory where the script will be saved.
    script_name (str): The name of the script (e.g., 'data_collection', 'preprocessing').
    purpose (str): The purpose of the script (e.g., 'Data extraction', 'Data cleaning').
    """
    if language == "r":
        extension = ".R"
        content = f"""# {purpose}

run_{script_name} <- function() {{
    # {purpose} code
    print('Running {script_name}...')
}}

# If you want to test this script independently, you can call the run() function directly.
if (interactive()) {{
    run_{script_name}()
}}
"""
    elif language == "python":
        extension = ".py"
        content = f"""# {purpose}

def run_{script_name}():
    # {purpose} code
    print("Running {script_name}...")

# If you want to test this script independently, you can call the run() function directly.
if __name__ == "__main__":
    run_{script_name}()
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

def create_workflow(language, folder_path):
    """
    Creates a workflow script that runs all steps in order.

    Parameters:
    language (str): "r" for R, "python" for Python.
    folder_path (str): The directory where the workflow script will be saved.
    """
    if language == "r":
        extension = ".R"
        content = """
# Workflow: Running all steps in order

# Load utility functions
source('utils.R')

# Run data collection
source('data_collection.R')

# Run preprocessing
source('preprocessing.R')

# Run modeling
source('modeling.R')

# Run visualization
source('visualization.R')
"""
    elif language == "python":
        extension = ".py"
        content = """
# Workflow: Running all steps in order

# Import utility functions
import utils

# Run data collection
import data_collection
data_collection.run_data_collection()

# Run preprocessing
import preprocessing
preprocessing.run_preprocessing()

# Run modeling
import modeling
modeling.run_modeling()

# Run visualization
import visualization
visualization.run_visualization()
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
        create_steps(language, folder_path, script_name, purpose)

    # Create the workflow script that runs all steps
    create_workflow(language, folder_path)

virtual_environment = "{{ cookiecutter.virtual_environment}}"
# Creates default scripts:
create_scripts(virtual_environment, "src")

# Run the script
subprocess.run(["python", "setup/create.py"])

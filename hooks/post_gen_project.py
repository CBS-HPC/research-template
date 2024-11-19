import os
import subprocess
import sys
import os

# Add the directory to sys.path
script_dir = "setup"
if script_dir not in sys.path:
    sys.path.append(script_dir)

def load_boilerplate(language,folder_path,script_type="step"):
    """
    Loads the boilerplate code from text files depending on the language (Python or R) and script type (step or workflow).
    """
    if script_type == "step":
        if language == "python":
            file_path = "python_boilerplate.txt"
        elif language == "r":
            file_path = "r_boilerplate.txt"
        else:
            raise ValueError("Invalid language choice. Please specify 'r' or 'python'.")
    elif script_type == "workflow":
        if language == "python":
            file_path = "python_workflow_boilerplate.txt"
        elif language == "r":
            file_path = "r_workflow_boilerplate.txt"
        else:
            raise ValueError("Invalid language choice. Please specify 'r' or 'python'.")
    else:
        raise ValueError("Invalid script_type. It must be 'step' or 'workflow'.")
    
    file_path = os.path.join(folder_path, file_path)
    with open(file_path, "r") as file:
        return file.read()

def create_step_script(language, folder_path, script_name, purpose):
    """
    Creates an individual script (R or Python) with the necessary structure.
    
    Parameters:
    language (str): "r" for R, "python" for Python.
    folder_path (str): The directory where the script will be saved.
    script_name (str): The name of the script (e.g., 'data_collection', 'preprocessing').
    purpose (str): The purpose of the script (e.g., 'Data extraction', 'Data cleaning').
    """
    # Load the boilerplate code from text files
    boilerplate = load_boilerplate(language,folder_path ,script_type="step")

    # Replace placeholders in the boilerplate code
    content = boilerplate.format(script_name=script_name, purpose=purpose)

    # Define the file path for saving the script
    if language == "python":
        extension = ".py"
    elif language == "r":
        extension = ".R"
    
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
    # Load the workflow boilerplate
    boilerplate = load_boilerplate(language,folder_path,script_type="workflow")

    # Define the file path for the workflow script
    if language == "python":
        extension = ".py"
    elif language == "r":
        extension = ".R"

    workflow_file_name = f"workflow{extension}"
    workflow_file_path = os.path.join(folder_path, workflow_file_name)

    # Write the workflow script content to the file
    with open(workflow_file_path, "w") as file:
        file.write(boilerplate)
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

virtual_environment = "{{ cookiecutter.virtual_environment}}"
# Creates default scripts:
create_project_scripts(virtual_environment, "src")

# Run the script
subprocess.run(["python", "setup/create.py"])

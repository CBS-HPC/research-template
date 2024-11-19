import os
import subprocess
import sys
import os
import shutil

# Add the directory to sys.path
script_dir = "setup"
if script_dir not in sys.path:
    sys.path.append(script_dir)

def copy_and_cleanup_templates(language, folder_path):
    """
    Copies the generated scripts from the template folders (R or Python) 
    to the specified folder path, and deletes the template folders afterwards.
    
    Parameters:
    language (str): "r" for R, "python" for Python.
    folder_path (str): The directory where the scripts will be saved.
    """
    # Define template folders for R and Python
    template_folders = {"r": "R", "python": "python"}

    # Ensure the folder exists
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    # Get the folder name based on the language
    template_folder = template_folders.get(language)
    if not template_folder:
        raise ValueError("Invalid language. Choose either 'r' or 'python'.")

    # Define the source and destination paths
    template_folder_path = os.path.join(os.getcwd(), template_folder)  # Assuming the templates are in the current directory
    if not os.path.exists(template_folder_path):
        raise FileNotFoundError(f"Template folder for {language} does not exist.")

    # Copy the files from the template folder to the specified folder path
    for file_name in os.listdir(template_folder_path):
        file_path = os.path.join(template_folder_path, file_name)
        if os.path.isfile(file_path):
            shutil.copy(file_path, folder_path)
            print(f"Copied: {file_name} to {folder_path}")

    # Delete the template folder after copying
    shutil.rmtree(template_folder_path)
    print(f"Deleted template folder: {template_folder_path}")


virtual_environment = "{{ cookiecutter.virtual_environment}}"
# Creates default scripts:
copy_and_cleanup_templates(virtual_environment, "src")

# Run the script
subprocess.run(["python", "setup/create.py"])

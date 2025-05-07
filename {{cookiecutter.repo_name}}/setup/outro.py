import os
import pathlib
import platform

from utils import *

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
        file_path = str(pathlib.Path(__file__).resolve().parent.parent / pathlib.Path(file_path))
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                results[file_path] = "Deleted"
            else:
                results[file_path] = "Not Found"
        except Exception as e:
            results[file_path] = f"Error: {e}"

    return results

#@ensure_correct_kernel
def main():
    os_type = platform.system().lower()
    if os_type == "windows":
        activate_to_delete = "./activate.sh"
        deactivate_to_delete = "./deactivate.sh"
    elif os_type == "darwin" or os_type == "linux":
        activate_to_delete = "./activate.ps1"
        deactivate_to_delete = "./deactivate.ps1"

    programming_language = load_from_env("PROGRAMMING_LANGUAGE",".cookiecutter")

    files_to_remove = ["./setup/project_setup.py","./run_setup.sh","./run_setup.ps1","./setup/intro.py","./setup/outro.py",activate_to_delete,deactivate_to_delete]

    if programming_language.lower() != 'r':
        files_to_remove.append("./src/renv_setup.R")

    # Deleting Setup scripts
    delete_files(files_to_remove)

    # Updating README
    creating_readme(programming_language = load_from_env("PROGRAMMING_LANGUAGE",".cookiecutter"))

    # Pushing to Git
    git_push(load_from_env("CODE_REPO",".cookiecutter")!= "None","README.md updated")

if __name__ == "__main__":
    
    # Ensure the working directory is the project root
    project_root = pathlib.Path(__file__).resolve().parent.parent.parent
    os.chdir(project_root)

    main()
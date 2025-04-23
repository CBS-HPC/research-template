import os
import platform

from utils import *
from readme_templates import *

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

@ensure_correct_kernel
def main():
    os_type = platform.system().lower()
    if os_type == "windows":
        activate_to_delete = "activate.sh"
        deactivate_to_delete = "deactivate.sh"
    elif os_type == "darwin" or os_type == "linux":
        activate_to_delete = "activate.ps1"
        deactivate_to_delete = "deactivate.ps1"

    # Deleting Setup scripts
    delete_files(["./setup/project_setup.py","./setup/code_templates.py","./setup/run_setup.sh","./setup/run_setup.ps1","./setup/intro.py","./setup/outro.py",activate_to_delete,deactivate_to_delete])

    # Updating README
    creating_readme()

    # Pushing to Git
    git_push(load_from_env("CODE_REPO",".cookiecutter")!= "None","README.md updated")

if __name__ == "__main__":
    main()
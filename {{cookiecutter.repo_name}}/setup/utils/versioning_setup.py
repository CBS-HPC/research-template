import sys
import os
import pathlib


# Ensure project root is in sys.path when run directly
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from utils.versioning_tools import *

@ensure_correct_kernel
def main():
    programming_language = load_from_env("PROGRAMMING_LANGUAGE",".cookiecutter")
    version_control = load_from_env("VERSION_CONTROL",".cookiecutter")
    repo_name = load_from_env("REPO_NAME",".cookiecutter")
    code_repo = load_from_env("CODE_REPO",".cookiecutter")
    remote_storage = load_from_env("REMOTE_STORAGE",".cookiecutter")

    # Setup Version Control
    setup_version_control(version_control,remote_storage,code_repo,repo_name)

if __name__ == "__main__":
    
    # Ensure the working directory is the project root
    project_root = pathlib.Path(__file__).resolve().parent.parent.parent
    os.chdir(project_root)
    
    main()
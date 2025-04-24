import sys
import shutil

from .versioning_tools import *

def set_program_path(programming_language):
    if programming_language.lower() not in ["python","none"]:
        exe_path = load_from_env(programming_language.upper())
        if not exe_path:
            exe_path = shutil.which(programming_language.lower())
            if exe_path:
                save_to_env(check_path_format(exe_path), programming_language.upper())
                save_to_env(get_version(programming_language), f"{programming_language.upper()}_VERSION",".cookiecutter")

    if not load_from_env("PYTHON"):
        save_to_env(sys.executable, "PYTHON")
        save_to_env(get_version("python"), "PYTHON_VERSION",".cookiecutter")

@ensure_correct_kernel
def main():
    programming_language = load_from_env("PROGRAMMING_LANGUAGE",".cookiecutter")
    version_control = load_from_env("VERSION_CONTROL",".cookiecutter")
    repo_name = load_from_env("REPO_NAME",".cookiecutter")
    code_repo = load_from_env("CODE_REPO",".cookiecutter")
    remote_storage = load_from_env("REMOTE_STORAGE",".cookiecutter")

    # Set to .env
    set_program_path(programming_language)

    # Setup Version Control
    setup_version_control(version_control,remote_storage,code_repo,repo_name)

if __name__ == "__main__":
    main()
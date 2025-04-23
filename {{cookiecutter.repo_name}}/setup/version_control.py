import sys
import shutil

from utils import *
from code_templates import *
from readme_templates import *

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
    project_name = load_from_env("PROJECT_NAME",".cookiecutter")
    version = load_from_env("VERSION",".cookiecutter")
    authors = load_from_env("AUTHORS",".cookiecutter")
    orcids = load_from_env("ORCIDS",".cookiecutter")
    project_description = load_from_env("PROJECT_DESCRIPTION",".cookiecutter")
    email = load_from_env("EMAIL",".cookiecutter")
    
    # Set to .env
    set_program_path(programming_language)

    # Create scripts and notebook
    create_scripts(programming_language, "./src")
    create_notebooks(programming_language, "./notebooks")
    
    # Create a citation file
    create_citation_file(project_name,version,authors,orcids,version_control,doi=None, release_date=None)

    # Creating README
    creating_readme(repo_name= repo_name, 
                    repo_user = repo_name, 
                    project_name = project_name,
                    project_description = project_description,
                    code_repo = code_repo,
                    programming_language = programming_language,
                    authors = authors,
                    orcids = orcids,
                    emails = email)
                    
    download_README_template(readme_file = "./DCAS template/README.md")

    # Setup Version Control
    setup_version_control(version_control,remote_storage,code_repo,repo_name)

if __name__ == "__main__":
    main()
import os
import sys
import pathlib

from utils import *


def create_folders():
    # Adjust or extend the list as needed
    folders = [
        "data/00_raw",
        "data/01_interim",
        "data/02_processed",
        "data/03_external",
    ]
    for f in folders:
        pathlib(f).mkdir(parents=True, exist_ok=True)
        # Optional: keep the dirs under version control
        (pathlib(f) / ".gitkeep").touch(exist_ok=True)



@ensure_correct_kernel
def main():

    # Ensure the working directory is the project root
    project_root = pathlib.Path(__file__).resolve().parent.parent.parent
    os.chdir(project_root)
    
    programming_language = load_from_env("PROGRAMMING_LANGUAGE",".cookiecutter")
    version_control = load_from_env("VERSION_CONTROL",".cookiecutter")
    project_name = load_from_env("PROJECT_NAME",".cookiecutter")
    version = load_from_env("VERSION",".cookiecutter")
    authors = load_from_env("AUTHORS",".cookiecutter")
    orcids = load_from_env("ORCIDS",".cookiecutter")

    # Set to .env
    set_program_path(programming_language)

    # Create scripts and notebook
    create_folders()
    create_scripts(programming_language, "./src")
    
    # Create a citation file
    create_citation_file(project_name,version,authors,orcids,version_control,doi=None, release_date=None)

    # Creating README
    creating_readme(programming_language)
    
                    
    download_README_template(readme_file = "./DCAS template/README.md")

if __name__ == "__main__":

    # Ensure the working directory is the project root
    project_root = pathlib.Path(__file__).resolve().parent.parent.parent
    os.chdir(project_root)

    main()
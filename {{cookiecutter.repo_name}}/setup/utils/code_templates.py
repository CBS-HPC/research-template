
from jinja2 import Environment, FileSystemLoader
import pathlib
import os
from textwrap import dedent
import pathlib

from .general_tools import *

package_installer(required_libraries = ['nbformat'])

import nbformat as nbf  # For creating Jupyter notebooks



template_env = Environment(
    loader=FileSystemLoader(str(pathlib.Path(__file__).resolve().parent / "j2_templates/code_templates")),
    trim_blocks=True,
    lstrip_blocks=True
)

ext_map = {
    "r": "R",
    "python": "py",
    "matlab": "m",
    "stata": "do",
    "sas": "sas"
}

language_dirs = {
    "r": "./R",
    "stata": "./stata",
    "python": "./src",
    "matlab": "./src",
    "sas": "./src"
}


def write_script(folder_path, script_name, extension, content):
    """
    Writes the content to a script file in the specified folder path.
    
    Parameters:
    folder_path (str): The folder where the script will be saved.
    script_name (str): The name of the script.
    extension (str): The file extension (e.g., ".py", ".R").
    content (str): The content to be written to the script.
    """
    # Create the folder if it doesn't exist
    full_folder_path = pathlib.Path(__file__).resolve().parent.parent.parent / folder_path
    full_folder_path.mkdir(parents=True, exist_ok=True)


    file_name = f"{script_name}.{extension}"
    file_path = os.path.join(folder_path, file_name)
    file_path= str(pathlib.Path(__file__).resolve().parent.parent.parent /  pathlib.Path(file_path))

    with open(file_path, "w") as file:
        if isinstance(content,str):
            file.write(content)
        else:
            nbf.write(content, file)

def create_script_from_template(language, template_name, script_name, context, subdir=None):
    template = template_env.get_template(f"{language}/{template_name}")
    rendered = template.render(**context)
    extension = template_name.split(".")[-2]
    folder_path = language_dirs.get(language.lower())
    if subdir:
        folder_path = os.path.join(folder_path, subdir)
    write_script(folder_path, script_name, extension, rendered)

def create_scripts(programming_language):
    
    programming_language = programming_language.lower()
    
    ext = ext_map.get(programming_language)
    
    if ext is None:
        raise ValueError(f"Unsupported language: {programming_language}")

    scripts = {
        "s00_main": "",
        "s01_install_dependencies": "Helper to install dependencies",
        "s02_utils": "Helper functions or utilities",
        "s03_data_collection": "Data extraction/scraping",
        "s04_preprocessing": "Data cleaning, transformation, feature engineering",
        "s05_modeling": "Training and evaluation of models",
        "s06_visualization": "Functions for plots and visualizations",
        "get_dependencies": ""
    }

    for script_name, purpose in scripts.items():
        if script_name == "s00_main":
            create_script_from_template(programming_language, f"main.{ext}.j2", script_name, {"script_name": script_name})
        elif script_name == "get_dependencies":
            create_script_from_template(programming_language, f"get_dependencies.{ext}.j2", script_name, {"script_name": script_name})
        elif script_name == "s01_install_dependencies":
            create_script_from_template(programming_language, f"s01_install_dependencies.{ext}.j2", script_name, {"script_name": script_name})
        else:
            create_script_from_template(programming_language, f"script.{ext}.j2", script_name, {"script_name": script_name, "purpose": purpose})

    notebook_templates = {
        "python": "s00_workflow.ipynb.j2",
        "r": "s00_workflow.Rmd.j2",
        "matlab": "s00_workflow.mlx.j2",
        "stata": "s00_workflow.ipynb.j2",
        "sas": "s00_workflow.ipynb.j2"
    }

    nb_template = notebook_templates.get(programming_language)
    if nb_template:
        create_script_from_template(programming_language, nb_template, "s00_workflow", {"script_name": "s00_workflow"})


@ensure_correct_kernel
def main():
    # Ensure the working directory is the project root
    project_root = pathlib.Path(__file__).resolve().parent.parent.parent
    os.chdir(project_root)
    
    # Create scripts and notebook
    create_scripts(load_from_env("PROGRAMMING_LANGUAGE",".cookiecutter"))

if __name__ == "__main__":

    # Ensure the working directory is the project root
    project_root = pathlib.Path(__file__).resolve().parent.parent.parent
    os.chdir(project_root)

    main()



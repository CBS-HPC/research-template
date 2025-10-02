import os
#from textwrap import dedent

from ..common import package_installer, ensure_correct_kernel, load_from_env, PROJECT_ROOT, language_dirs, ext_map
from .jinja import set_jinja_templates, write_script

package_installer(required_libraries = ['nbformat','jinja2'])

template_env = set_jinja_templates("j2/code")


def create_script_from_template(programming_language, folder_path, template_name, script_name, context, subdir=None):
    template = template_env.get_template(f"{programming_language}/{template_name}")
    rendered = template.render(**context)
    extension = template_name.split(".")[-2]
    if subdir:
        folder_path = os.path.join(folder_path, subdir)
    write_script(folder_path, script_name, extension, rendered)

def create_scripts(programming_language):
    
    programming_language = programming_language.lower()
    folder_path = language_dirs.get(programming_language)
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
            create_script_from_template(programming_language, folder_path,  f"main.{ext}.j2", script_name, {"script_name": script_name})
        elif script_name == "get_dependencies":
            create_script_from_template(programming_language, folder_path,  f"get_dependencies.{ext}.j2", script_name, {"script_name": script_name})
        elif script_name == "s01_install_dependencies":
            create_script_from_template(programming_language, folder_path,  f"s01_install_dependencies.{ext}.j2", script_name, {"script_name": script_name})
        elif script_name == "s02_utilss":
            create_script_from_template(programming_language, folder_path,  f"s02_utils.{ext}.j2", script_name, {"script_name": script_name})    
        else:
            create_script_from_template(programming_language, folder_path,  f"script.{ext}.j2", script_name, {"script_name": script_name, "purpose": purpose})

    notebook_templates = {
        "python": "s00_workflow.ipynb.j2",
        "r": "s00_workflow.Rmd.j2",
        "matlab": "s00_workflow.ipynb.j2",
        #"matlab": "s00_workflow.mlx.j2",
        "stata": "s00_workflow.ipynb.j2",
        "sas": "s00_workflow.ipynb.j2"
    }


    # Note books
    nb_template = notebook_templates.get(programming_language)
    if nb_template:
        create_script_from_template(programming_language, folder_path,  nb_template, "s00_workflow", {"script_name": "s00_workflow"})

    tests_map = {
        "python": ("./tests", "py"),
        "r": ("./tests/testthat", "R"),
        "matlab": ("./tests", "m"),
        "stata": ("./tests", "do")
    }


    # unit test templates
    folder_path, extension = tests_map[programming_language]
    template_name = f"test_template.{extension}.j2"

    for base in scripts.keys():
        create_script_from_template(programming_language, folder_path,  template_name, f"test_{base}", {"base": base})    

@ensure_correct_kernel
def main():
    # Ensure the working directory is the project root
    os.chdir(PROJECT_ROOT)
    
    # Create scripts and notebook
    create_scripts(load_from_env("PROGRAMMING_LANGUAGE",".cookiecutter"))

if __name__ == "__main__":
    main()


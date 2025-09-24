import os
import pathlib

from .general_tools import *
from .readme_templates import main as update_readme_main
from .get_dependencies import main as get_setup_dependencies_main
from .jinja_tools import *

template_env = set_jinja_templates("j2_templates/example_templates")

def render_template(language, template_name, context):
    try:
        template = template_env.get_template(f"{language}/{template_name}")
        return template.render(**context)
    except Exception as e:
        print(f"Warning: Could not render template '{template_name}' for language '{language}': {e}")
        return None

def create_example(project_language):
    project_language = project_language.lower()
    ext = ext_map.get(project_language)
    if ext is None:
        raise ValueError(f"Unsupported language: {project_language}")
    folder_path = language_dirs.get(project_language)
    
    script_keys = [
        "s00_main",
        "s01_install_dependencies",
        "s02_utils",
        "s03_data_collection",
        "s04_preprocessing",
        "s05_modeling",
        "s06_visualization"
    ]
    
    for script_name in script_keys:
        template_file = f"{script_name}.{ext}.j2"
        context = {
            "script_name": script_name,
            "purpose": script_name.replace("s01_", "install_dependencies")
                                   .replace("s02_", "utils")
                                   .replace("s03_", "Data collection")
                                   .replace("s04_", "Preprocessing")
                                   .replace("s05_", "Modeling")
                                   .replace("s06_", "Visualization")
        }
        rendered = render_template(project_language, template_file, context)
        if rendered is not None:
            write_script(folder_path, script_name, ext, rendered)
        else:
            print(f"Skipped {script_name} due to missing or faulty template.")

@ensure_correct_kernel
def main():
    # Ensure the working directory is the project root
    os.chdir(PROJECT_ROOT)
    
    programming_language = load_from_env("PROGRAMMING_LANGUAGE",".cookiecutter")
  
    # Create scripts and notebook
    print(f"loading {programming_language} code example")
    create_example(programming_language)
    get_setup_dependencies_main()
    update_readme_main()

    
if __name__ == "__main__":
    main()
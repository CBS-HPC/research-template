import os
from subprocess import DEVNULL
#from contextlib import contextmanager
#from functools import wraps
import pathlib

from ..common import package_installer, PROJECT_ROOT

#package_installer(required_libraries = ['jinja2','nbformat'])

# Jinja template functions (MOVE to own file)
from jinja2 import Environment, FileSystemLoader
import nbformat

def set_jinja_templates(template_folder:str):
    
    template_env = Environment(
    loader=FileSystemLoader(str(pathlib.Path(__file__).resolve().parent / template_folder)),
    trim_blocks=True,
    lstrip_blocks=True
    )

    return template_env

def patch_jinja_templates(template_folder: str):
    template_dir = pathlib.Path(__file__).resolve().parent / template_folder

    for file in template_dir.rglob("*.j2"):
        with open(file, "r", encoding="utf-8") as f:
            content = f.read()

        original = content
        content = content.replace("END_RAW_MARKER", "endraw").replace("RAW_MARKER", "raw")

        if content != original:
            print(f"✅ Patched: {file}")
            with open(file, "w", encoding="utf-8") as f:
                f.write(content)

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
    full_folder_path = PROJECT_ROOT / folder_path
    full_folder_path.mkdir(parents=True, exist_ok=True)


    file_name = f"{script_name}.{extension}"
    file_path = os.path.join(folder_path, file_name)
    file_path= str(PROJECT_ROOT /  pathlib.Path(file_path))

    with open(file_path, "w") as file:
        if isinstance(content,str):
            file.write(content)
        else:
            nbformat.write(content, file)


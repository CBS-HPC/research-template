import os
import sys
import os
import pathlib

# Ensure the project root is in sys.path
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from utils import *

def main():
    creating_readme(programming_language = load_from_env("PROGRAMMING_LANGUAGE",".cookiecutter"))


if __name__ == "__main__":
    
    # Change to project root directory
    project_root = pathlib.Path(__file__).resolve().parent.parent.parent
    os.chdir(project_root)
    
    main()

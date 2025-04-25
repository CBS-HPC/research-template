import os
import pathlib
import sys

# Ensure the project root is in sys.path
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from utils import *

@ensure_correct_kernel
def main():
    versioning_setup.main()
    repo_setup.main()


if __name__ == "__main__":
    
    # Ensure the working directory is the project root
    project_root = pathlib.Path(__file__).resolve().parent.parent.parent
    os.chdir(project_root)
    
    main()
import os
import pathlib
import sys
#base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
#setup_path =  os.path.join(base_path, "setup") 
#sys.path.append(setup_path)


# Ensure the project root is in sys.path
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

# Ensure the working directory is the project root
project_root = pathlib.Path(__file__).resolve().parent.parent
os.chdir(project_root)

from utils import *

@ensure_correct_kernel
def main():
    #import version_control
    #import remote_repository
    
    # Change to project root directory
    project_root = pathlib.Path(__file__).resolve().parent.parent.parent
    os.chdir(project_root)

    version_control.main()
    
    remote_repository.main()


if __name__ == "__main__":
    main()
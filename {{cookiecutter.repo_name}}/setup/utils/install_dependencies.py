import subprocess
import sys
import re
import importlib.util
import pathlib

# Ensure the project root is in sys.path
#sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from utils import *

def parse_dependencies(file_path="dependencies.txt"):
    required_libraries = []
    try:
        with open(file_path, 'r') as f:
            lines = f.readlines()
        
        # Flag to start reading dependencies section
        reading_dependencies = False
        
        for line in lines:
            # Check for the start of the dependencies section
            if 'Dependencies:' in line:
                reading_dependencies = True
                continue  # Skip the "Dependencies:" line
            
            # If we are in the dependencies section, extract the library names
            if reading_dependencies:
                # Stop reading if we encounter an empty line or another section
                if line.strip() == '':
                    break
                
                # Regex to match package names and versions
                match = re.match(r'(\S+)(==\S+)?', line.strip())
                if match:
                    lib_name = match.group(1)
                    version = match.group(2) if match.group(2) else None
                    
                    # Ignore libraries with 'Not available' as they don't need to be installed
                    if version != 'Not available':
                        required_libraries.append(f"{lib_name}{version if version else ''}")
                
    except FileNotFoundError:
        print(f"Error: The file {file_path} was not found.")
        return []

    return required_libraries

def is_standard_library(lib_name):
    spec = importlib.util.find_spec(lib_name)
    return spec is not None and spec.origin is None  # Origin None means it's built-in

def install_dependencies(required_libraries):
    # Get list of installed libraries
    installed_libraries = subprocess.check_output([sys.executable, '-m', 'pip', 'freeze']).decode().splitlines()

    # Check and install missing libraries
    for lib in required_libraries:
        try:
            # Extract library name (without version) for checking
            lib_name = lib.split('==')[0]
            
            # Skip installation for standard libraries
            if is_standard_library(lib_name):
                print(f"Skipping installation of standard library: {lib_name}")
                continue

            # Check if the library is already installed
            if not any(lib.lower() in installed_lib.lower() for installed_lib in installed_libraries):
                print(f"Installing {lib}...")
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', lib])
            else:
                print(f"{lib} is already installed.")
        except subprocess.CalledProcessError as e:
            print(f"Failed to install {lib}: {e}")

@ensure_correct_kernel
def main(dependencies_file="dependencies.txt"):
    # Parse the dependencies from the text file
    required_libraries = parse_dependencies(dependencies_file)
    
    # Install the missing dependencies
    if required_libraries:
        install_dependencies(required_libraries)
    else:
        print("No dependencies found to install.")


if __name__ == "__main__":
    
    # Ensure the working directory is the project root
    project_root = pathlib.Path(__file__).resolve().parent.parent.parent
    os.chdir(project_root)

    main()  # Specify the dependencies file here

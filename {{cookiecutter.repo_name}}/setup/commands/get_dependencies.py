import os
import subprocess
import ast
import sys
import sysconfig
from datetime import datetime
import importlib.metadata
import yaml
from typing import Optional, Dict, Set, List
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from utils import *

def resolve_parent_module(module_name):
    if '.' in module_name:
        return module_name.split('.')[0]
    return module_name

@ensure_correct_kernel
def get_setup_dependencies(folder_path: str = None, file_name: str = "dependencies.txt", requirements_file:str=None, install_cmd:str=None):
    
    def get_dependencies_from_file(python_files):
        used_packages = set()
        for file in python_files:
            with open(file, "r") as f:
                tree = ast.parse(f.read(), filename=file)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            used_packages.add(resolve_parent_module(alias.name))
                    elif isinstance(node, ast.ImportFrom) and node.module:
                        used_packages.add(resolve_parent_module(node.module))
        
        # List Python standard library modules by checking files in the standard library path
        std_lib_path = sysconfig.get_paths()["stdlib"]
        standard_libs = []
        for root, dirs, files in os.walk(std_lib_path):
            for file in files:
                if file.endswith(".py") or file.endswith(".pyc"):
                    standard_libs.append(os.path.splitext(file)[0])

        installed_packages = {}
        for package in used_packages:
            try:
                version = importlib.metadata.version(package)
                installed_packages[package] = version
            except importlib.metadata.PackageNotFoundError:
                if package not in standard_libs and package not in sys.builtin_module_names:
                    installed_packages[package] = "Not available" 
        
        python_script_names = {os.path.splitext(os.path.basename(file))[0] for file in python_files}
        valid_packages = {package: version for package, version in installed_packages.items()
                        if not (version == "Not available" and package in python_script_names)}
        return valid_packages
    
    def process_requirements(requirements_file: str) -> Dict[str, str]:
        
        def extract_conda_dependencies(env_data: dict) -> List[str]:
            packages = []
            for item in env_data.get('dependencies', []):
                if isinstance(item, str):
                    packages.append(item.split("=")[0])  # Extract package name before "="
                elif isinstance(item, dict) and 'pip' in item:
                    packages.extend([pkg.split("==")[0] for pkg in item['pip'] if isinstance(pkg, str)])
            return packages

        print(f"Processing requirements from: {requirements_file}")
        installed_packages = {}
        try:
            if requirements_file.endswith(".txt"):
                with open(requirements_file, "r") as f:
                    packages = [line.split("==")[0].strip() for line in f.readlines() if line.strip() and not line.startswith("#")]
            elif requirements_file.endswith((".yml", ".yaml")):
                with open(requirements_file, "r") as f:
                    env_data = yaml.safe_load(f)
                    packages = extract_conda_dependencies(env_data)

            for package in packages:
                try:
                    version = importlib.metadata.version(package)
                    installed_packages[package] = version
                except importlib.metadata.PackageNotFoundError:
                    installed_packages[package] = "Not available"
        except Exception as e:
            print(f"Error processing requirements file: {e}")
        return installed_packages

    if folder_path is None:
        folder_path = os.path.dirname(os.path.abspath(__file__))
    elif folder_path == "":
        folder_path =  os.getcwd()
    
    print(f"Scanning folder: {folder_path}")
    python_files = []
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.endswith(".py"):
                python_files.append(os.path.join(root, file))

    if not python_files:
        print("No Python files found in the specified folder.")
        return

    if requirements_file:
        installed_packages = process_requirements(requirements_file)
    else:
        installed_packages  = get_dependencies_from_file(python_files)

    # Write to file
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    relative_python_files = [os.path.relpath(file, folder_path) for file in python_files]
    python_version = subprocess.check_output([sys.executable, '--version']).decode().strip()

    if os.path.exists(os.path.dirname(file_name)):
        output_file = file_name
    else: 
        output_file = os.path.join(folder_path,"dependencies.txt")
    
    with open(output_file, "w") as f:
        f.write("Software version:\n")
        f.write(f"{python_version}\n\n")
        f.write(f"Timestamp: {timestamp}\n\n")
        f.write("Files checked:\n")
        f.write("\n".join(relative_python_files) + "\n\n")
        
        if install_cmd:
            f.write("Install Command:\n")
            f.write(f"{install_cmd}\n\n")

        f.write("Dependencies:\n")
        for package, version in installed_packages .items():
            f.write(f"{package}=={version}\n")

    print(f"{file_name} successfully generated at {output_file}")

def main():
    get_setup_dependencies()

if __name__ == "__main__":
    main()
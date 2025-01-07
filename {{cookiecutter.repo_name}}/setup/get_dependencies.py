import os
import subprocess
import ast
import sys
import sysconfig

from datetime import datetime
import importlib.util
import importlib.metadata

def resolve_parent_module(module_name):
    """Resolve and return the top-level module for submodules."""
    if '.' in module_name:
        return module_name.split('.')[0]
    return module_name

def get_setup_dependencies(folder_path: str = None, file_name: str = "REQUIREMENTS.txt"):
    if folder_path is None:
        folder_path = os.path.dirname(os.path.abspath(__file__))
    print(f"Scanning folder: {folder_path}")

    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'])
    except subprocess.CalledProcessError as e:
        print(f"Failed to upgrade pip: {e}")
        return

    python_files = []
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.endswith(".py"):
                python_files.append(os.path.join(root, file))

    if not python_files:
        print("No Python files found in the specified folder.")
        return

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
    
    # Get the path to the standard library
    std_lib_path = sysconfig.get_paths()["stdlib"]
    # List Python standard library modules by checking files in the standard library path

    python_version = subprocess.check_output([sys.executable, '--version']).decode().strip()
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

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    relative_python_files = [os.path.relpath(file, folder_path) for file in python_files]

    output_file = os.path.join(folder_path, file_name)
    with open(output_file, "w") as f:
        f.write("Software version:\n")
        f.write(f"{python_version}\n\n")
        f.write(f"Timestamp: {timestamp}\n\n")
        f.write("Files checked:\n")
        f.write("\n".join(relative_python_files) + "\n\n")
        f.write("Dependencies:\n")
        for package, version in valid_packages.items():
            f.write(f"{package}=={version}\n")

    print(f"{file_name} successfully generated at {output_file}")

if __name__ == "__main__":
    get_setup_dependencies()

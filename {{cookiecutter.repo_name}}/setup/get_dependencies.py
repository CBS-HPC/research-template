import os
import subprocess
import ast
from datetime import datetime

def get_setup_dependencies(folder_path:str=None, file_name:str = "REQUIREMENTS.txt"):
    # If folder_path is not provided, use the folder of the current script
    if folder_path is None:
        folder_path = os.path.dirname(os.path.abspath(__file__))
    print(f"Scanning folder: {folder_path}")

    # Ensure pip is up-to-date
    try:
        subprocess.check_call([os.sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'])
    except subprocess.CalledProcessError as e:
        print(f"Failed to upgrade pip: {e}")
        return

    # Find all .py files in the folder and subfolders
    python_files = []
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.endswith(".py"):
                python_files.append(os.path.join(root, file))

    if not python_files:
        print("No Python files found in the specified folder.")
        return

    # Scan the Python files for imported packages
    used_packages = set()
    for file in python_files:
        with open(file, "r") as f:
            tree = ast.parse(f.read(), filename=file)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        used_packages.add(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    used_packages.add(node.module)

    # Install and fetch versions for the used packages
    installed_packages = {}
    for package in used_packages:
        try:
            # Try to get the version of the package
            version = subprocess.check_output([os.sys.executable, '-m', 'pip', 'show', package]).decode('utf-8')
            version_line = [line for line in version.splitlines() if line.startswith('Version')][0]
            installed_packages[package] = version_line.split(" ")[1]
        except subprocess.CalledProcessError:
            # If the package is not installed, add it with 'Not available'
            installed_packages[package] = "Not available"

    # Check for Python scripts corresponding to "Not available" packages
    python_script_names = {os.path.splitext(os.path.basename(file))[0] for file in python_files}
    valid_packages = {}

    for package, version in installed_packages.items():
        if not (version == "Not available" and package in python_script_names):
           valid_packages[package] = version
        
    # Collect Python version
    python_version = subprocess.check_output([os.sys.executable, '--version']).decode().strip()

    # Get the current timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Collect the list of files checked (relative paths)
    relative_python_files = [os.path.relpath(file, folder_path) for file in python_files]

    # Write the required information to the setup_dependencies.txt
    output_file = os.path.join(folder_path, file_name)
    with open(output_file, "w") as f:
        f.write(f"{python_version}\n\n")
        f.write(f"Timestamp: {timestamp}\n\n")
        f.write("Files checked:\n")
        f.write("\n".join(relative_python_files) + "\n\n")
        f.write("Dependencies:\n")
        for package, version in valid_packages.items():
            f.write(f"{package}=={version}\n")


    print(f"{file_name} successfully generated at {output_file}")
if __name__ == "__main__":
    get_setup_dependencies(None)


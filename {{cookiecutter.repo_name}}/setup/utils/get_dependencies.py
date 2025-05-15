import os
import subprocess
import ast
import sys
import sysconfig
from datetime import datetime
import importlib
from typing import Dict, List
import pathlib

from .virenv_tools import *

# Determine file extension based on programming language
ext_map = {
    "r": "R",
    "python": "py",
    "matlab": "m",
    "stata": "do",
    "sas": "sas"
}

def run_get_dependencies(programming_language, folder_path="./src"):
    """
    Runs the get_dependencies.* script for the specified programming language.

    Args:
        programming_language (str): Programming language name ('python', 'r', etc.)
        folder_path (str): The folder where get_dependencies.* is located (default: 'setup').

    Returns:
        str: Output from running the dependency script or error message.
    """
    programming_language = programming_language.lower()
    ext = ext_map.get(programming_language)

    if ext is None:
        return f"Unsupported programming language: {programming_language}"

    script_filename = f"get_dependencies.{ext}"
    script_path = os.path.join(folder_path, script_filename)

    if not os.path.exists(script_path):
        return f"Dependency script not found: {script_path}"

    try:
        if programming_language == "python":
            with open(script_path, "r") as f:
                script_content = f.read()  
            return run_script(programming_language, script_command=script_content)

        elif programming_language == "r":
            script_path = make_safe_path( script_path)
            cmd = " -f " + script_path
            return run_script(programming_language, script_command=cmd)

        elif programming_language == "matlab":
            return run_script(programming_language, script_command=script_path)

        elif programming_language == "sas":
            return run_script(programming_language, script_command=script_path)

        elif programming_language == "stata":
            # Special case: Stata scripts may behave differently
            return run_script(programming_language, script_command=script_path)

        else:
            return f"Unsupported language in script execution: {programming_language}"

    except Exception as e:
        return f"Failed to run dependency script: {str(e)}"

def resolve_parent_module(module_name):
    if '.' in module_name:
        return module_name.split('.')[0]
    return module_name

def get_setup_dependencies(folder_path: str = None, file_name: str = "dependencies.txt"):
    
    def get_dependencies_from_file(python_files):
        used_packages = set()

        for file in python_files:
            try:
                with open(file, "r", encoding="utf-8") as f:
                    tree = ast.parse(f.read(), filename=file)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            used_packages.add(resolve_parent_module(alias.name))
                    elif isinstance(node, ast.ImportFrom) and node.module:
                        used_packages.add(resolve_parent_module(node.module))
            except (SyntaxError, UnicodeDecodeError) as e:
                print(f"Skipping {file} due to parse error: {e}")
        
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

    print(f"Scanning folder: {folder_path}")
    python_files = []
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.endswith(".py"):
                python_files.append(os.path.join(root, file))

    if not python_files:
        print("No Python files found in the specified folder.")
        return

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
        f.write("Dependencies:\n")
        for package, version in installed_packages .items():
            f.write(f"{package}=={version}\n")

    print(f"{file_name} successfully generated at {output_file}")

def setup_renv(programming_language,msg:str):
    if programming_language.lower() == "r":
        # Call the setup script using the function
        script_path = make_safe_path(str(pathlib.Path(__file__).resolve().parent.parent.parent / pathlib.Path("./src/get_dependencies.R")))
        project_root = make_safe_path(str(pathlib.Path(__file__).resolve().parent.parent.parent / pathlib.Path("./src")))
        cmd = " -f " + script_path + " --args " + project_root
        output = run_script("r", cmd)
        print(output)
        print(msg)

def setup_matlab(programming_language,msg:str):
    if programming_language.lower() == "matlab":
        src_folder = make_safe_path(str(pathlib.Path(__file__).resolve().parent.parent.parent / pathlib.Path("./src")))
        cmd = f"""
        "addpath('{src_folder}'); get_dependencies"
        """
        output = run_script("matlab", cmd)
        print(output)
        print(msg)

def setup_stata(programming_language,msg:str):
    if programming_language.lower() == "stata":
        # Call the setup script using the function
        script_path = make_safe_path(str(pathlib.Path(__file__).resolve().parent.parent.parent / pathlib.Path("./src/get_dependencies.do")))
        cmd = f"do {script_path}"
        output = run_script("stata", cmd)
        print(output)
        print(msg)

def update_env_files():
    programming_language = load_from_env("PROGRAMMING_LANGUAGE",".cookiecutter")
    requirements_file = load_from_env("REQUIREMENT_FILE",".cookiecutter")
    repo_name = load_from_env("REPO_NAME",".cookiecutter")
    create_requirements_txt("requirements.txt")
    if requirements_file == "requirements.txt":
        create_conda_environment_yml(r_version = load_from_env("R_VERSION", ".cookiecutter") if programming_language.lower() == "r" else None)
    elif requirements_file == "environment.yml": 
        export_conda_env(repo_name)

def update_setup_dependency():
    print("Screening './setup' for dependencies")
    setup_folder = str(pathlib.Path(__file__).resolve().parent.parent.parent / pathlib.Path("./setup"))
    setup_file = str(pathlib.Path(__file__).resolve().parent.parent.parent / pathlib.Path("./setup/dependencies.txt"))
    get_setup_dependencies(folder_path=setup_folder,file_name =setup_file) 

def update_src_dependency():
    programming_language = load_from_env("PROGRAMMING_LANGUAGE",".cookiecutter")
    print("Screening './src' for dependencies")
    src_folder = str(pathlib.Path(__file__).resolve().parent.parent.parent / pathlib.Path("./src"))
    if programming_language.lower() == "python":
        src_file = str(pathlib.Path(__file__).resolve().parent.parent.parent / pathlib.Path("./src/dependencies.txt"))
        get_setup_dependencies(folder_path=src_folder,file_name=src_file)
    elif programming_language.lower() == "r":
        setup_renv(programming_language,"/renv and .lock file has been updated")
    elif programming_language.lower() == "matlab":
        #print(run_get_dependencies(programming_language, folder_path=src_folder))
        setup_matlab(programming_language,"Tracking Matlab dependencies")
    elif programming_language.lower() == "stata":
        setup_stat(programming_language,"Tracking Stata dependencies")
    else:
        print("not implemented yet")

@ensure_correct_kernel
def main():
    
    print("Updating 'requirements.txt','environment.yml'")
    update_env_files()

    # Run dependencies search
    update_setup_dependency()
    update_src_dependency()

if __name__ == "__main__":
    # Ensure the working directory is the project root
    project_root = pathlib.Path(__file__).resolve().parent.parent.parent
    os.chdir(project_root)
    main()

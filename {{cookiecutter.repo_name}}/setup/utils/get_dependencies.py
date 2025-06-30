import os
import subprocess
import ast
import sys
import sysconfig
from datetime import datetime
import importlib
from typing import Dict, List
import pathlib

from .virenv_tools import export_conda_env
from .general_tools import *
from .toml_tools import *

package_installer(required_libraries =  ['nbformat','pyyaml'])


import yaml
import nbformat
  # TOML support
if sys.version_info < (3, 11):
    import toml
else:
    import tomllib as toml
    import tomli_w


def create_requirements_txt(requirements_file: str = "requirements.txt"):
    """
    Writes pip freeze output to requirements.txt and ensures all installed packages
    are tracked in uv.lock (by running `uv add` on any missing).
    """

    project_root = pathlib.Path(__file__).resolve().parent.parent.parent
    requirements_path = project_root / requirements_file
    uv_lock_path = project_root / "uv.lock"

    # Step 1: Get pip freeze output
    result = subprocess.run([sys.executable, "-m", "pip", "freeze"], capture_output=True, text=True)
    if result.returncode != 0:
        print("❌ Error running pip freeze:", result.stderr)
        return

    # Step 2: Parse pip freeze output
    frozen_lines = result.stdout.strip().splitlines()
    installed_pkgs = {
        line.split("==")[0].lower(): line for line in frozen_lines if "==" in line
    }

    # Step 3: Write pip freeze output to requirements.txt
    with open(requirements_path, "w", encoding="utf-8") as f:
        f.write("\n".join(frozen_lines) + "\n")
    print("📄 requirements.txt has been created successfully.")

    if pathlib.Path("uv.lock").exists():
        # Step 4: Parse uv.lock to get already-locked packages
        locked_pkgs = set()
        if uv_lock_path.exists() and uv_lock_path.stat().st_size > 0:
            try:
                with open(uv_lock_path, "rb") as f:
                    uv_data = toml.load(f)
                    for pkg in uv_data.get("package", []):
                        if isinstance(pkg, dict) and "name" in pkg:
                            locked_pkgs.add(pkg["name"].lower())
            except Exception as e:
                print(f"⚠️ Failed to parse uv.lock: {e}")

        # Step 5: Add missing packages to uv.lock
        missing_from_lock = [pkg for pkg in installed_pkgs if pkg not in locked_pkgs]
        if missing_from_lock:
            print(f"🔄 Adding missing packages to uv.lock: {missing_from_lock}")
            for pkg in missing_from_lock:
                try:
                    #subprocess.run(["uv", "add", pkg], check=True,     
                    subprocess.run([sys.executable, "-m","uv", "add", pkg], check=True,
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                except subprocess.CalledProcessError as e:
                    print(f"❌ Failed to add {pkg} via uv: {e}")

def create_conda_environment_yml(env_name,r_version=None,requirements_file:str="requirements.txt", output_file:str="environment.yml"):
    """
    Creates a Conda environment.yml based on a pip requirements.txt file, 
    the current Python version, and optionally an R version.
    
    Parameters:
    - requirements_file (str): Path to the pip requirements.txt file.
    - output_file (str): Path to output the generated environment.yml file (default 'environment.yml').
    - r_version (str, optional): R version string like "R version 4.4.3" (default None).
    """
    requirements_file = str(pathlib.Path(__file__).resolve().parent.parent.parent / pathlib.Path(requirements_file))
    output_file = str(pathlib.Path(__file__).resolve().parent.parent.parent / pathlib.Path(output_file))


    if not os.path.exists(requirements_file):
        raise FileNotFoundError(f"Requirements file not found: {requirements_file}")

    # Get the current Python version
    version_output = subprocess.check_output([sys.executable, '--version']).decode().strip()
    python_version = version_output.split()[1]  # Get '3.10.12'

    # Read the requirements.txt
    with open(requirements_file, "r", encoding="utf-8") as f:
        pip_dependencies = [line.strip() for line in f if line.strip() and not line.startswith("#")]

    # Build the basic dependencies list
    conda_dependencies = [f'python={python_version}']

    # If R version is provided, extract version number and add R base package
    if r_version:
        try:
            # Expect input like "R version 4.4.3"
            r_version_number = r_version.split()[-1]  # Get '4.4.3'
            conda_dependencies.append(f'r-base={r_version_number}')
        except Exception as e:
            print(f"Warning: Could not parse R version. Got error: {e}")

    # Add pip dependencies
    conda_dependencies.append({'pip': pip_dependencies})

    # Create environment.yml structure
    conda_env = {
        'name': {env_name},
        'dependencies': conda_dependencies
    }

    # Write the environment.yml
    with open(output_file, "w", encoding="utf-8") as f:
        yaml.dump(conda_env, f, default_flow_style=False, sort_keys=False)

    print(f"✅ Conda environment file created: {output_file}")

def tag_env_file(env_file: str = "environment.yml"):
    # Paths
    root = pathlib.Path(__file__).resolve().parent.parent.parent
    env_path = root / env_file

    if not env_path.exists():
        print(f"❌ {env_file} not found.")
        return

    raw_rules = read_toml_json(folder = root,json_filename =  "platform_rules.json",tool_name = "platform_rules", toml_path = "pyproject.toml")

    if not raw_rules:
        print("ℹ️ No platform rules found. Skipping tagging.")
        return

    sys_to_conda = {
        "win32": "win",
        "darwin": "osx",
        "linux": "linux"
    }

    # Translate rules
    platform_rules = {}
    for pkg, sys_platform in raw_rules.items():
        conda_selector = sys_to_conda.get(sys_platform)
        if conda_selector:
            platform_rules[pkg.lower()] = conda_selector

    # Read environment.yml
    with open(env_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    in_pip_section = False
    updated_lines = []

    for line in lines:
        stripped = line.strip()

        # Detect pip block
        if stripped == "- pip":
            in_pip_section = True
            updated_lines.append(line)
            continue

        # End of pip block if indentation ends
        if in_pip_section and not line.startswith("  ") and line.strip():
            in_pip_section = False

        if stripped.startswith("- "):
            pkg = stripped[2:].split("==")[0].split(">=")[0].strip().lower()
            platform = platform_rules.get(pkg)
            if platform:
                updated_lines.append(line.rstrip() + f"  # [{platform}]\n")
            else:
                updated_lines.append(line)
        else:
            updated_lines.append(line)

    # Write back
    with open(env_path, "w", encoding="utf-8") as f:
        f.writelines(updated_lines)

    print(f"✅ Updated {env_file} with Conda-style platform tags")

def tag_requirements_txt(requirements_file: str = "requirements.txt"):
    # Resolve paths
    root = pathlib.Path(__file__).resolve().parent.parent.parent
    requirements_path = root / requirements_file
    
    platform_rules = read_toml_json(folder = root,json_filename =  "platform_rules.json",tool_name = "platform_rules", toml_path = "pyproject.toml")

    if not platform_rules:
        print("ℹ️ No platform rules found. Skipping tagging.")
        return

    if not requirements_path.exists():
        raise FileNotFoundError(f"❌ Requirements file not found: {requirements_path}")

    # Read the requirements.txt
    with open(requirements_path, "r", encoding="utf-8") as f:
        lines = f.read().strip().splitlines()

    filtered_lines = []
    for line in lines:
        clean_line = line.strip()
        if not clean_line or clean_line.startswith("#"):
            filtered_lines.append(line)
            continue

        pkg = clean_line.split("==")[0].split(">=")[0].split("<=")[0].strip().lower()
        if pkg in platform_rules:
            platform = platform_rules[pkg]
            filtered_lines.append(f"{clean_line} ; sys_platform == \"{platform}\"")
        else:
            filtered_lines.append(clean_line)

    with open(requirements_path, "w", encoding="utf-8") as f:
        f.write("\n".join(filtered_lines) + "\n")

    print(f"✅ requirements.txt updated with platform tags: {requirements_path}")

def run_get_dependencies(programming_language):
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

    folder_path = language_dirs.get(programming_language)

    script_filename = f"get_dependencies.{ext}"
    script_path = os.path.join(folder_path, script_filename)

    if not os.path.exists(script_path):
        return f"Dependency script not found: {script_path}"

    try:
        if programming_language == "python":
            with open(script_path, "r") as f:
                script_content = f.read()  
            return run_script(programming_language, script_command=script_content)

        elif programming_language in ["r","matlab","stata","sas"]: 
            
            if programming_language == "r":
                script_path = make_safe_path(script_path,"r")
            
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
    
    def extract_code_from_notebook(path):
        code_cells = []
        try:
            nb = nbformat.read(path, as_version=4)
            for cell in nb.cells:
                if cell.cell_type == "code":
                    code_cells.append(cell.source)
        except Exception as e:
            print(f"Could not parse notebook {path}: {e}")
        return "\n".join(code_cells)

    def get_dependencies_from_file(python_files):
        used_packages = set()

        for file in python_files:
            try:
                if file.endswith(".ipynb"):
                    code = extract_code_from_notebook(file)
                else:
                    with open(file, "r", encoding="utf-8") as f:
                        code = f.read()

                tree = ast.parse(code, filename=file)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            used_packages.add(resolve_parent_module(alias.name))
                    elif isinstance(node, ast.ImportFrom) and node.module:
                        used_packages.add(resolve_parent_module(node.module))

            except (SyntaxError, UnicodeDecodeError, FileNotFoundError) as e:
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

    if folder_path is None:
        folder_path = os.path.dirname(os.path.abspath(__file__))

    print(f"Scanning folder: {folder_path}")
    python_files = []
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.endswith(".py") or file.endswith(".ipynb"):
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

    return installed_packages

def setup_renv(programming_language,msg:str):
    if programming_language.lower() == "r":
        # Call the setup script using the function
        script_path = make_safe_path(str(pathlib.Path(__file__).resolve().parent.parent.parent / pathlib.Path("./R/get_dependencies.R")),"r")
        project_root = make_safe_path(str(pathlib.Path(__file__).resolve().parent.parent.parent / pathlib.Path("./R")),"r")
        cmd = [script_path, "--args", project_root]
        output = run_script("r", cmd)
        print(output)
        print(msg)

def setup_matlab(programming_language,msg:str):
    if programming_language.lower() == "matlab":
        code_path = make_safe_path(str(pathlib.Path(__file__).resolve().parent.parent.parent / pathlib.Path("./src")),"matlab")
        cmd = f"""
        "addpath({code_path}); get_dependencies"
        """
        output = run_script("matlab", cmd)
        print(output)
        print(msg)

def setup_stata(programming_language,msg:str):
    if programming_language.lower() == "stata":
        # Call the setup script using the function
        script_path = make_safe_path(str(pathlib.Path(__file__).resolve().parent.parent.parent / pathlib.Path("./stata/do/get_dependencies.do")),"stata")
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
        create_conda_environment_yml(repo_name, r_version = load_from_env("R_VERSION", ".cookiecutter") if programming_language.lower() == "r" else None)
    elif requirements_file == "environment.yml": 
        export_conda_env(repo_name)

    tag_requirements_txt(requirements_file="requirements.txt")
    tag_env_file(env_file = "environment.yml")

def update_setup_dependency():
    print("Screening './setup' for dependencies")
    setup_folder = str(pathlib.Path(__file__).resolve().parent.parent.parent / pathlib.Path("./setup"))
    setup_file = str(pathlib.Path(__file__).resolve().parent.parent.parent / pathlib.Path("./setup/dependencies.txt"))
    _ = get_setup_dependencies(folder_path=setup_folder,file_name =setup_file) 

def update_code_dependency():
    programming_language = load_from_env("PROGRAMMING_LANGUAGE",".cookiecutter")
    if programming_language.lower() == "python":
        print("Screening './src' for dependencies")
        code_path = str(pathlib.Path(__file__).resolve().parent.parent.parent / pathlib.Path("./src"))
        code_file = str(pathlib.Path(__file__).resolve().parent.parent.parent / pathlib.Path("./src/dependencies.txt"))
        _ = get_setup_dependencies(folder_path=code_path,file_name=code_file)
    elif programming_language.lower() == "r":
        print("Screening './R' for dependencies")
        setup_renv(programming_language,"/renv and .lock file has been updated")
    elif programming_language.lower() == "matlab":
        print("Screening './src' for dependencies")
        #print(run_get_dependencies(programming_language))
        setup_matlab(programming_language,"Tracking Matlab dependencies")
    elif programming_language.lower() == "stata":
        print("Screening './stata' for dependencies")
        setup_stata(programming_language,"Tracking Stata dependencies")
    else:
        print("not implemented yet")

@ensure_correct_kernel
def main():
    
    print("Updating 'requirements.txt','environment.yml'")
    update_env_files()

    # Run dependencies search
    update_setup_dependency()
    update_code_dependency()

if __name__ == "__main__":
    # Ensure the working directory is the project root
    project_root = pathlib.Path(__file__).resolve().parent.parent.parent
    os.chdir(project_root)
    main()

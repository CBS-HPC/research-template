import os
import subprocess
import sys
import platform
import urllib.request
import pathlib
import json

from .general_tools import *

package_installer(required_libraries =  ['pyyaml'])

import yaml

# Virtual Environment
def setup_virtual_environment(version_control, python_env_manager, r_env_manager, repo_name, conda_r_version, conda_python_version, install_path = "./bin/miniconda3"):
    """
    Create a virtual environment for Python or R based on the specified programming language.

    Parameters:
    - repo_name: str, name of the virtual environment.
    - programming_language: str, 'python' or 'R' to specify the language for the environment.
    """    
    install_path = str(pathlib.Path(__file__).resolve().parent.parent.parent / pathlib.Path(install_path))

    env_name = None
  
    if python_env_manager.lower() == "conda" or r_env_manager.lower() == "conda":
        conda_packages = set_conda_packages(version_control,python_env_manager,r_env_manager,conda_python_version,conda_r_version)
        env_name = setup_conda(install_path=install_path, repo_name=repo_name, conda_packages=conda_packages, env_file=None, conda_r_version=conda_r_version, conda_python_version=conda_python_version)
    elif python_env_manager.lower() == "venv":
        env_name = create_venv_env(repo_name)

    if env_name:
        env_name = env_name.replace("\\", "/")

    return env_name

# Common Env Functions
def load_env_file(extensions = ['.yml', '.txt']): # FIX ME - NOT USED
    
    def get_file_path(extensions = ['.yml', '.txt']):
        """
        Prompt the user to provide the path to a .yml or .txt file and check if the file exists and is the correct format.
        
        Returns:
        - str: Validated file path if the file exists and has the correct extension.
        """

        # Prompt the user for the file path
        file_path = input("Please enter the path to a .yml or .txt file: ").strip()
            
        # Check if the file exists
        if not os.path.isfile(file_path):
            print("The file does not exist. Please try again.")
            return None
            
        # Check the file extension
        _, file_extension = os.path.splitext(file_path)
        if file_extension.lower() not in extensions:
            print(f"Invalid file format. The file must be a {extensions}")
            return None
        
        # If both checks pass, return the valid file path
        return file_path

    if '.txt' in extensions and '.yml' in extensions:
        msg = "Do you want to create a virtual environment from a pre-existing 'environment.yaml' or 'requirements.txt' file? (yes/no):" 
        error= "no 'environment.yaml' or 'requirements.txt' file was loaded"
    elif '.txt' in extensions:
        msg = "Do you want to create a virtual environment from a pre-existing 'requirements.txt' file? (yes/no):"
        error= "no 'requirements.txt' file was loaded"
    elif '.yml' in extensions:
        msg = "Do you want to create a virtual environment from a pre-existing 'environment.yaml' file? (yes/no):"
        error= "no 'environment.yaml' file was loaded"
    
    confirm = ask_yes_no(msg)

    if confirm:
        env_file = get_file_path(extensions)
        if env_file is None:
            print(error)
        return env_file
    else:
        return None

# Conda Functions:
def setup_conda(install_path:str,repo_name:str, conda_packages:list = [], env_file:str = None, conda_r_version:str = None, conda_python_version:str = None):
    
    install_path = os.path.abspath(install_path)

    if not is_installed('conda','Conda'):
        if not install_miniconda(install_path):
            return False

    # Get the absolute path to the environment
    env_path = str(pathlib.Path(__file__).resolve().parent.parent.parent / pathlib.Path(f"./bin/conda/{repo_name}"))

    if env_file and (env_file.endswith('.yaml') or env_file.endswith('.txt')):
        if env_file.endswith('.txt'):
            env_file = generate_env_yml(repo_name,env_file)
        update_env_yaml(env_file, repo_name, conda_packages)
        command = ['conda', 'env', 'create', '-f', env_file, '--prefix', env_path]
        msg = f'Conda environment "{repo_name}" created successfully from {env_file}.'
    else:
        command = ['conda', 'create', '--yes', '--prefix', env_path, '-c', 'conda-forge']

        command.extend(conda_packages)
        msg = f'Conda environment "{repo_name}" was created successfully. The following conda packages were installed: {conda_packages}.'

    flag = create_conda_env(command,msg)

    if not flag and (conda_python_version or conda_r_version):
        if conda_python_version:
            command = [item for item in command if conda_python_version not in item]
            print(f"Choice of Python version {conda_python_version} has been cancelled due to installation problems")
        if conda_r_version:
            command = [item for item in command if conda_r_version not in item]
            print(f"Choice of Python version {conda_r_version} has been cancelled due to installation problems")

        flag = create_conda_env(command,msg)

    if flag:
        export_conda_env(env_path)
        
       # env_path = os.path.relpath(env_path)
        save_to_env(env_path,"CONDA_ENV_PATH")
        return env_path
    else:
        return None

def set_conda_packages(version_control,python_env_manager,r_env_manager,conda_python_version,conda_r_version):

    install_packages = []
        
    if python_env_manager.lower() == "conda":
        if conda_python_version:
            install_packages.extend([f'python={conda_python_version}'])
        else:
            install_packages.extend(['python'])

    if r_env_manager.lower() == "conda":
        if conda_r_version:
            install_packages.extend([f'r-base={conda_r_version}'])
        else:
            install_packages.extend(['r-base'])

    
    os_type = platform.system().lower()    
    
    if version_control.lower() in ['git','dvc','datalad'] and not is_installed('git', 'Git'):
        install_packages.extend(['git'])   
    
    if version_control.lower()  == "datalad":
        if not is_installed('rclone', 'Rclone'):    
            install_packages.extend(['rclone'])

        if os_type in ["darwin","linux"] and not is_installed('git-annex', 'git-annex'):
            install_packages.extend(['git-annex'])

    return install_packages

def export_conda_env(env_path, output_file="environment.yml"):
    """
    Export the details of a conda environment to a YAML file.
    
    Parameters:
    - env_name: str, name of the conda environment to export.
    - output_file: str, name of the output YAML file. Defaults to 'environment.yml'.
    """
    def update_conda_env_file(file_path: str):
        # Get the current working directory
        current_dir = os.path.abspath(os.getcwd())
        
        # Load the existing environment.yml file
        with open(file_path, 'r') as f:
            env_data = yaml.safe_load(f)

        # Check if 'prefix' and 'name' are defined
        if 'prefix' in env_data and 'name' in env_data:
            # Get the absolute path from the prefix
            prefix_abs_path = env_data['prefix']
            
            # Extract the last part of the path for the 'name'
            new_name = os.path.basename(prefix_abs_path)
            
            # Make the prefix relative to the current working directory
            prefix_relative_path = os.path.relpath(prefix_abs_path, current_dir)
            
            # Update the 'name' and 'prefix'
            env_data['name'] = new_name
            env_data['prefix'] = prefix_relative_path

            # Save the updated file
            with open(file_path, 'w') as f:
                yaml.dump(env_data, f, default_flow_style=False)
        else:
            print(f"'{file_path}' does not contain both 'name' and 'prefix' fields.")

    output_file= str(pathlib.Path(__file__).resolve().parent.parent.parent / pathlib.Path(output_file))

    try:
        # Use subprocess to run the conda export command
        with open(output_file, 'w') as f:
            #subprocess.run(['conda', 'env', 'export', '-n', env_name], stdout=f, check=True)  
            subprocess.run(['conda', 'env', 'export', '--prefix', env_path], stdout=f, check=True)      
        
        update_conda_env_file(output_file)
        print(f"Conda environment '{env_path}' exported to {output_file}.")

    except subprocess.CalledProcessError as e:
        print(f"Failed to export conda environment: {e}")
    except FileNotFoundError:
        print("Conda is not installed or not found in the system path.")
    except Exception as e:
        print(f"An error occurred: {e}")

def init_conda():
    """
    Initializes Conda for the user's shell by running `conda init` and starting a new interactive shell session.

    Returns:
    - bool: True if Conda shell initialization is successful, False otherwise.
    """
    try:
        subprocess.run(["conda", "init"], check=True)
        print("Conda shell initialization complete.")
        return True

    except Exception as e:
        print(f"Failed to initialize Conda shell: {e}")
        return False

def install_miniconda(install_path):
    """
    Downloads and installs Miniconda3 to a specified location based on the operating system.
    
    Parameters:
    - install_path (str): The absolute path where Miniconda3 should be installed.

    Returns:
    - bool: True if installation is successful, False otherwise.
    """ 
    os_type = platform.system().lower()
    installer_name = None
    download_dir = os.path.dirname(install_path)  # One level up from the install_path
    installer_path = None
    
    if os_type == "windows":
        installer_name = "Miniconda3-latest-Windows-x86_64.exe"
        url = f"https://repo.anaconda.com/miniconda/{installer_name}"
        installer_path = os.path.join(download_dir, installer_name)
        install_command = [installer_path, "/InstallationType=JustMe", f"/AddToPath=0", f"/RegisterPython=0", f"/S", f"/D={install_path}"]
        
    elif os_type == "darwin":  # macOS
        installer_name = "Miniconda3-latest-MacOSX-arm64.sh" if platform.machine() == "arm64" else "Miniconda3-latest-MacOSX-x86_64.sh"
        url = f"https://repo.anaconda.com/miniconda/{installer_name}"
        installer_path = os.path.join(download_dir, installer_name)
        install_command = ["bash", installer_path, "-b","-f","-p", install_path]
        
    elif os_type == "linux":
        installer_name = "Miniconda3-latest-Linux-x86_64.sh"
        url = f"https://repo.anaconda.com/miniconda/{installer_name}"
        installer_path = os.path.join(download_dir, installer_name)
        install_command = ["bash", installer_path, "-b","-f","-p", install_path]
        
    else:
        print("Unsupported operating system.")
        return False
    
    try:
        print(f"Downloading {installer_name} from {url} to {download_dir}...")
        urllib.request.urlretrieve(url, installer_path)
        print("Download complete.")
        
        print("Installing Miniconda3...")
        subprocess.run(install_command, check=True)
        if installer_path and os.path.exists(installer_path):
            os.remove(installer_path)
        
        if exe_to_path("conda",os.path.join(install_path, "bin")): 
            if not init_conda():
                return False
        else:
            return False
        
        if is_installed('conda','Conda'):
            print("Miniconda3 installation complete.")
            return True
        else:
            return False
    
    except Exception as e:
        if installer_path and os.path.exists(installer_path):
            os.remove(installer_path)
        print(f"Failed to install Miniconda3: {e}")
        return False

def create_conda_env(command,msg):
    """
    Create a conda environment from an environment.yml file with a specified name.
    
    Parameters:
    - env_file: str, path to the environment YAML file. Defaults to 'environment.yml'.
    - env_name: str, optional name for the new environment. If provided, overrides the name in the YAML file.
    """
    try:
        # Run the command
        subprocess.run(command, check=True)
        print(msg)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to create conda environment: {e}")
    except FileNotFoundError:
        print("Conda is not installed or not found in the system path.")
    except Exception as e:
        print(f"An error occurred: {e}")
    return False

def generate_env_yml(env_name,requirements_path):
    """Generate an environment.yml file using a requirements.txt file."""
    env_file = 'environment.yml'
    yml_content = f"""
        name: {env_name}
        channels:
        - conda-forge
        dependencies:
        - python>=3.5
        - anaconda
        - pip
        - pip:
            - -r file:{requirements_path}
        """
    with open(env_file, 'w') as yml_file:
        yml_file.write(yml_content)
    print(f"Generated environment.yml file using {requirements_path}.")
    return env_file

def update_env_yaml(env_file:str, repo_name:str, conda_packages:list=[], pip_packages:list=[]):
    """
    Updates an existing environment.yml file to:
    - Change the environment name to `repo_name`
    - Add additional packages from `conda_packages` list
    - Add additional packages from `pip_packages` list

    Parameters:
    env_file (str): Path to the existing environment.yml file
    repo_name (str): The new environment name (usually repo name)
    conda_packages (list): List of additional Conda packages to install
    pip_packages (list): List of additional packages to install

    Returns:
    None
    """
    # Load the existing environment.yml file
    with open(env_file, 'r') as file:
        env_data = yaml.safe_load(file)

    # Change the environment name based on the repo_name
    env_data['name'] = repo_name

    # If there is a 'dependencies' section, add Conda packages to it
    if 'dependencies' in env_data:
        # Make sure dependencies is a list
        if not isinstance(env_data['dependencies'], list):
            env_data['dependencies'] = []
        
        # Add Conda packages if not already present
        for package in conda_packages:
            if package not in env_data['dependencies']:
                env_data['dependencies'].append(package)
    else:
        # If no dependencies section exists, create it
        env_data['dependencies'] = conda_packages

    # Add pip packages under the pip section
    pip_section = None
    for item in env_data['dependencies']:
        # Check if there's an existing pip section
        if isinstance(item, dict) and 'pip' in item:
            pip_section = item['pip']
            break

    if pip_section is not None:
        # Append pip packages to the existing pip section
        for pip_package in pip_packages:
            if pip_package not in pip_section:
                pip_section.append(pip_package)
    else:
        # Create a new pip section
        if pip_packages:
            env_data['dependencies'].append({'pip': pip_packages})

    # Save the updated environment.yml
    with open(env_file, 'w') as file:
        yaml.dump(env_data, file, default_flow_style=False)

    print(f"Updated {env_file} with new environment name '{repo_name}', added Conda packages, and additional packages.")

# Venv and Virtualenv Functions
def create_venv_env(env_name):
    """Create a Python virtual environment using venv and install packages."""
    try:
        # Get the absolute path to the environment
        env_path = str(pathlib.Path(__file__).resolve().parent.parent.parent / pathlib.Path(f"./bin/venv/{env_name}"))

        # Create the virtual environment
        subprocess.run([sys.executable, '-m', 'venv', env_path], check=True)
        print(f'Venv environment "{env_path}" for Python created successfully.')
        
        save_to_env(env_path,"VENV_ENV_PATH")

        # Return the path to the virtual environment
        return env_path

    except subprocess.CalledProcessError as e:
        print(f"Error: A subprocess error occurred while creating the virtual environment or installing packages: {e}")
        return None
    except Exception as e:
        print(f"Error: An unexpected error occurred: {e}")
        return None

def create_requirements_txt(requirements_file:str="requirements.txt"):

    requirements_file = str(pathlib.Path(__file__).resolve().parent.parent.parent / pathlib.Path(requirements_file))

    # Get the Python executable path from sys.executable
    python_executable = sys.executable
    
    # Use subprocess to run pip freeze and capture the output
    result = subprocess.run([python_executable, "-m", "pip", "freeze"], capture_output=True, text=True)
    
    # Check if the pip freeze command was successful
    if result.returncode == 0:
        # Write the output of pip freeze to a requirements.txt file
        with open(requirements_file, "w") as f:
            f.write(result.stdout)
        print("requirements.txt has been created successfully.")
    else:
        print("Error running pip freeze:", result.stderr)

def create_conda_environment_yml(r_version=None,requirements_file:str="requirements.txt", output_file:str="environment.yml"):
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
        'name': 'auto_env',
        'dependencies': conda_dependencies
    }

    # Write the environment.yml
    import yaml
    with open(output_file, "w", encoding="utf-8") as f:
        yaml.dump(conda_env, f, default_flow_style=False, sort_keys=False)

    print(f"✅ Conda environment file created: {output_file}")

def tag_env_file(env_file: str = "environment.yml", platform_rules_file: str = "platform_rules.json"):
    # Paths
    root = pathlib.Path(__file__).resolve().parent.parent.parent
    env_path = root / env_file
    rules_path = root / platform_rules_file

    if not env_path.exists():
        print(f"❌ {env_file} not found.")
        return

    if not rules_path.exists():
        print(f"❌ {platform_rules_file} not found.")
        return

    # Load platform rules (sys_platform -> conda selector map)
    with open(rules_path, "r", encoding="utf-8") as f:
        raw_rules = json.load(f)

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

    print(f"✅ Updated {env_file} with Conda-style platform tags using {platform_rules_file}")

def tag_requirements_txt(requirements_file: str = "requirements.txt",platform_rules_file: str = "platform_rules.json"):
    # Resolve paths
    root = pathlib.Path(__file__).resolve().parent.parent.parent
    requirements_path = root / requirements_file
    rules_path = root / platform_rules_file

    # Load platform-specific rules
    if rules_path.exists():
        with open(rules_path, "r", encoding="utf-8") as f:
            platform_rules = json.load(f)
    else:
        platform_rules = {}

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
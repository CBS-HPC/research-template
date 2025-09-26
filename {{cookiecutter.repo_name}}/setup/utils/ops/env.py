import os
import subprocess
import sys
import platform
import urllib.request
import pathlib
import shutil
from ..general_tools import package_installer, ask_yes_no, is_installed, save_to_env, exe_to_path, install_uv,PROJECT_ROOT

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
    install_path = str(PROJECT_ROOT / pathlib.Path(install_path))

    env_name = None
  
    if python_env_manager.lower() == "conda" or r_env_manager.lower() == "conda":
        conda_packages = set_conda_packages(version_control,python_env_manager,r_env_manager,conda_python_version,conda_r_version)
        env_name = setup_conda(install_path=install_path, repo_name=repo_name, conda_packages=conda_packages, env_file=None, conda_r_version=conda_r_version, conda_python_version=conda_python_version)
    elif python_env_manager.lower() == "venv":
        env_name = create_venv_env()

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
    env_path = str(PROJECT_ROOT / pathlib.Path(f"./.conda"))

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

    install_packages.extend(['uv'])
    
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
    Export the details of a conda environment to a YAML file using its path.
    
    Parameters:
    - env_path: str or Path, full path to the conda environment directory.
    - output_file: str or Path, output YAML file path (default 'environment.yml').
    """
    env_path = os.path.abspath(env_path)
    output_file = os.path.abspath(output_file)

    def update_conda_env_file(file_path):
        with open(file_path, 'r') as f:
            env_data = yaml.safe_load(f)

        if env_data is None:
            print(f"Failed to parse environment YAML at {file_path}")
            return

        if 'prefix' in env_data:
            prefix_path = env_data['prefix']
            env_data['name'] = os.path.basename(prefix_path)
            # Optional: remove 'prefix' to avoid hard-coding paths
            del env_data['prefix']

            with open(file_path, 'w') as f:
                yaml.dump(env_data, f, default_flow_style=False)

    try:
        with open(output_file, 'w') as f:
            subprocess.run(['conda', 'env', 'export', '--prefix', env_path], stdout=f, check=True)
        
        update_conda_env_file(output_file)
        print(f"Environment exported to: {output_file}")
    except subprocess.CalledProcessError as e:
        print(f"Failed to export conda environment: {e}")
    except FileNotFoundError:
        print("Conda is not installed or not found in PATH.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

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
    os_type = platform.system().lower()
    download_dir = os.path.dirname(install_path)
    installer_name = None
    installer_path = None

    if os_type == "windows":
        # Override to C:\Users\<username>\miniconda3
        user_home = pathlib.Path.home()
        install_path = str(user_home / "miniconda3")
        print(f"Windows detected — overriding install path to: {install_path}")

        download_dir = os.path.dirname(install_path)
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)

        installer_name = "Miniconda3-latest-Windows-x86_64.exe"
        url = f"https://repo.anaconda.com/miniconda/{installer_name}"
        installer_path = os.path.join(download_dir, installer_name)

        install_path_win = os.path.abspath(install_path).replace("/", "\\")

        if os.path.exists(install_path_win):
            print(f"Removing existing directory before install: {install_path_win}")
            shutil.rmtree(install_path_win)

        install_command = f'"{installer_path}" /S /InstallationType=JustMe /AddToPath=0 /RegisterPython=0 /D={install_path_win}'

    elif os_type == "darwin":
        installer_name = "Miniconda3-latest-MacOSX-arm64.sh" if platform.machine() == "arm64" else "Miniconda3-latest-MacOSX-x86_64.sh"
        url = f"https://repo.anaconda.com/miniconda/{installer_name}"
        installer_path = os.path.join(download_dir, installer_name)
        install_command = ["bash", installer_path, "-b", "-f", "-p", install_path]

    elif os_type == "linux":
        installer_name = "Miniconda3-latest-Linux-x86_64.sh"
        url = f"https://repo.anaconda.com/miniconda/{installer_name}"
        installer_path = os.path.join(download_dir, installer_name)
        install_command = ["bash", installer_path, "-b", "-f", "-p", install_path]

    else:
        print("Unsupported operating system.")
        return False

    try:
        print(f"Downloading {installer_name} from {url} to {download_dir}...")
        urllib.request.urlretrieve(url, installer_path)
        print("Download complete.")

        print("Installing Miniconda3...")

        if os_type == "windows":
            subprocess.run(install_command, check=True, shell=True)
        else:
            subprocess.run(install_command, check=True)

        # Remove installer after installation
        if installer_path and os.path.exists(installer_path):
            os.remove(installer_path)

        conda_executable = os.path.join(install_path, "Scripts", "conda.exe") if os_type == "windows" else os.path.join(install_path, "bin", "conda")

        if not os.path.exists(conda_executable):
            print("Miniconda installation failed: conda executable not found.")
            return False

        if exe_to_path("conda",os.path.dirname(conda_executable )): 
            if not init_conda():
                return False
        else:
            return False
        
        if is_installed('conda','Conda'):
            print("Miniconda3 installation complete.")
            return True
        else:
            return False
        
    except subprocess.CalledProcessError as e:
        print(f"Installation failed during subprocess execution: {e}")
    except Exception as e:
        print(f"Installation failed: {e}")
    finally:
        if installer_path and os.path.exists(installer_path):
            os.remove(installer_path)

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

def create_venv_env():
    """
    Create a Python virtual environment using uv if available; otherwise, use venv.
    If the virtual environment already exists, do nothing.
    """
    env_path = PROJECT_ROOT / ".venv"

    if env_path.exists():
        save_to_env(str(env_path), "VENV_ENV_PATH")
        return str(env_path)

    used_uv = False

    if install_uv():  # Only try uv if available
        try:
            env = os.environ.copy()
            env["UV_LINK_MODE"] = "copy"
            subprocess.run([sys.executable, "-m", "uv", "venv", str(env_path)], check=True, env=env)
            print(f'✅ Virtual environment created at "{env_path}" using uv.')
            used_uv = True
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("⚠️ uv failed to create the virtual environment. Falling back to venv.")

    if not used_uv:
        try:
            subprocess.run([sys.executable, "-m", "venv", str(env_path)], check=True)
            print(f'✅ Virtual environment created at "{env_path}" using venv.')
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to create virtual environment using venv: {e}")
            return None
        except Exception as e:
            print(f"❌ Unexpected error while creating the virtual environment: {e}")
            return None

    save_to_env(str(env_path), "VENV_ENV_PATH")

    return str(env_path)

import os
import subprocess
import sys
import platform
#from textwrap import dedent
import shutil
import urllib.request

required_libraries = ['python-dotenv','pyyaml'] 
installed_libraries = subprocess.check_output([sys.executable, '-m', 'pip', 'freeze']).decode().splitlines()

for lib in required_libraries:
    try:
        # Check if the library is already installed
        if not any(lib.lower() in installed_lib.lower() for installed_lib in installed_libraries):
            print(f"Installing {lib}...")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', lib])
    except subprocess.CalledProcessError as e:
        print(f"Failed to install {lib}: {e}")

from dotenv import dotenv_values, load_dotenv
import yaml

def get_relative_path(target_path):

    if target_path:
        current_dir = os.getcwd()
        absolute_target_path = os.path.abspath(target_path)
        
        # Check if target_path is a subpath of current_dir
        if os.path.commonpath([current_dir, absolute_target_path]) == current_dir:
            # Create a relative path if it is a subpath
            relative_path = os.path.relpath(absolute_target_path, current_dir)

            if relative_path:
                return relative_path
    return target_path

def ask_yes_no(question):
    """
    Prompt the user with a yes/no question and validate the input.

    Args:
        question (str): The question to display to the user.

    Returns:
        bool: True if the user confirms (yes/y), False if the user declines (no/n).
    """
    while True:
        response = input(question).strip().lower()
        if response in {"yes", "y"}:
            return True
        elif response in {"no", "n"}:
            return False
        else:
            print("Invalid response. Please answer with 'yes' or 'no'.")

def load_from_env(env_var: str, env_file=".env"):
    """
    Loads an environment variable's value from a .env file.
    
    Args:
        env_var (str): The name of the environment variable to load.
        env_file (str): The path to the .env file (default is ".env").
        
    Returns:
        str or None: The value of the environment variable if found, otherwise None.
    """
    # Attempt to read directly from the .env file
    if os.path.exists(env_file):
        env_values = dotenv_values(env_file)
        if env_var.upper() in env_values:
            return env_values[env_var.upper()]
    
    # If not found directly, load the .env file into the environment
    load_dotenv(env_file, override=True)
    return os.getenv(env_var.upper())

def save_to_env(env_var: str, env_name: str, env_file=".env"):
    """
    Saves or updates an environment variable in a .env file (case-insensitive for variable names).
    
    Args:
        env_var (str): The value of the environment variable to save.
        env_name (str): The name of the environment variable (case-insensitive).
        env_file (str): The path to the .env file. Defaults to ".env".
    """
    if env_var is None:
        return
    # Standardize the variable name for comparison
    env_name_upper = env_name.strip().upper()
    
    # Read the existing .env file if it exists
    env_lines = []
    if os.path.exists(env_file):
        with open(env_file, 'r') as file:
            env_lines = file.readlines()

    # Check if the variable exists (case-insensitive) and update it
    variable_exists = False
    for i, line in enumerate(env_lines):
        # Split each line to isolate the variable name
        if "=" in line:
            existing_name, _ = line.split("=", 1)
            if existing_name.strip().upper() == env_name_upper:
                env_lines[i] = f"{env_name_upper}={env_var}\n"  # Preserve original case in name
                variable_exists = True
                break

    # If the variable does not exist, append it
    if not variable_exists:
        env_lines.append(f"{env_name_upper}={env_var}\n")
    
    # Write the updated lines back to the file
    with open(env_file, 'w') as file:
        file.writelines(env_lines)

def exe_to_path(executable: str = None, path: str = None,env_file:str=".env"):
    """
    Adds the path of an executable binary to the system PATH permanently.
    """
    os_type = platform.system().lower()
    
    if not executable or not path:
        print("Executable and path must be provided.")
        return False

    if os.path.exists(path):
        # Add to current session PATH
        os.environ["PATH"] += os.pathsep + path

        if os_type == "windows":
            # Use setx to set the environment variable permanently in Windows
            subprocess.run(["setx", "PATH", f"{path};%PATH%"], check=True)
        else:
            # On macOS/Linux, add the path to the shell profile file
            profile_file = os.path.expanduser("~/.bashrc")  # or ~/.zshrc depending on the shell
            with open(profile_file, "a") as file:
                file.write(f'\nexport PATH="{path}:$PATH"')

        # Check if executable is found in the specified path
        resolved_path = shutil.which(executable)
        
        if resolved_path:
            resolved_path = os.path.dirname(resolved_path)

        if resolved_path == path:
            print(f"{executable} binary is added to PATH and resolved correctly: {path}")
            path = get_relative_path(path)
            save_to_env(path, executable.upper())
            load_dotenv(env_file, override=True)
            return True
        elif resolved_path:
            print(f"{executable} binary available at a wrong path: {resolved_path}")
            print(f"Instead of: {path}")
            resolved_path = get_relative_path(resolved_path)
            save_to_env(resolved_path, executable.upper())
            load_dotenv(env_file, override=True)
            return True
        else:
            print(f"{executable} binary is not found in the specified PATH: {path}")
            return False
    else:
        print(f"{executable}: path does not exist: {path}")
        return False

def remove_from_env(path: str):
    """
    Removes a specific path from the system PATH for the current session and permanently if applicable.
    
    Args:
        path (str): The path to remove from the PATH environment variable.

    Returns:
        bool: True if the path was successfully removed, False otherwise.
    """
    if not path:
        print("No path provided to remove.")
        return False

    # Normalize the path for comparison
    path = os.path.normpath(path)
    
    # Split the current PATH into a list
    current_paths = os.environ["PATH"].split(os.pathsep)
    
    # Remove the specified path
    filtered_paths = [p for p in current_paths if os.path.normpath(p) != path]
    os.environ["PATH"] = os.pathsep.join(filtered_paths)

    # Update PATH permanently
    os_type = platform.system().lower()
    if os_type == "windows":
        # Use setx to update PATH permanently on Windows
        try:
            subprocess.run(["setx", "PATH", os.environ["PATH"]], check=True)
            print(f"Path {path} removed permanently on Windows.")
        except subprocess.CalledProcessError as e:
            print(f"Failed to update PATH permanently on Windows: {e}")
            return False
    else:
        # On macOS/Linux, remove the path from the shell profile file
        profile_file = os.path.expanduser("~/.bashrc")  # or ~/.zshrc depending on the shell
        if os.path.exists(profile_file):
            try:
                with open(profile_file, "r") as file:
                    lines = file.readlines()
                with open(profile_file, "w") as file:
                    for line in lines:
                        if f'export PATH="{path}:$PATH"' not in line.strip():
                            file.write(line)
                print(f"Path {path} removed permanently in {profile_file}.")
            except Exception as e:
                print(f"Failed to update {profile_file}: {e}")
                return False
    return True

def exe_to_env(executable: str = None, path: str = None, env_file: str = ".env"):
    """
    Adds the path of an executable binary to an environment file.
    """
    if not executable:
        print("Executable must be provided.")
        return False

    # Attempt to resolve path if not provided
    if not path or not os.path.exists(path):
        path = os.path.dirname(shutil.which(executable))
    
    if path:
        # Save to environment file
        save_to_env(path, executable.upper())  # Assuming `save_to_env` is defined elsewhere
        load_dotenv(env_file, override=True)

        # Check if executable is found in the specified path
        resolved_path = shutil.which(executable)
        if resolved_path and os.path.dirname(resolved_path) == path:
            print(f"{executable} binary is added to the environment and resolved correctly: {path}")
            save_to_env(path, executable.upper())  # Assuming `save_to_env` is defined elsewhere
            load_dotenv(env_file, override=True)
            return True
        elif resolved_path:
            print(f"{executable} binary available at a wrong path: {resolved_path}")
            save_to_env(os.path.dirname(resolved_path), executable.upper())
            load_dotenv(env_file, override=True) 
            return True
        else:
            print(f"{executable} binary is not found in the specified environment PATH: {path}")
            return False
    else:
        print(f"{executable}:path does not exist: {path}")
        return False

def is_installed(executable: str = None, name: str = None):
    
    if name is None:
        name = executable

    # Check if both executable and name are provided as strings
    if not isinstance(executable, str) or not isinstance(name, str):
        raise ValueError("Both 'executable' and 'name' must be strings.")
    
    path = load_from_env(executable)
    if path:
        path = os.path.abspath(path)

    if path and os.path.exists(path):
        return exe_to_path(executable, path)    
    elif path and not os.path.exists(path):
        remove_from_env(path)

    if shutil.which(executable):
        return exe_to_path(executable, os.path.dirname(shutil.which(executable)))
    else:
        print(f"{name} is not on Path")
        return False

def set_from_env():
  
    is_installed('git')
    is_installed('datalad')
    is_installed('git-annex')
    is_installed('rclone')
    is_installed('git-annex-remote-rclone')

def search_apps(app: str):
    """
    Search for executables matching partial app names in the system's PATH.

    Args:
        pattern (str): Partial name of the application to search for.

    Returns:
        list: A list of paths matching the executable pattern.
    """
    found_paths = []
    system_paths = os.environ["PATH"].split(os.pathsep)  # Split PATH into directories

    for directory in system_paths:
        if os.path.isdir(directory):  # Check if the PATH directory exists
            try:
                for file in os.listdir(directory):
                    # Match only if the entire pattern is in the filename
                    if app.lower() in file.lower():
                        full_path = os.path.join(directory, file)
                        if os.access(full_path, os.X_OK):  # Check if file is executable
                            found_paths.append(full_path)
            except PermissionError:
                continue  # Skip directories with permission issues

    if not found_paths:
        print(f"No executables found for app '{app}'.")
    return found_paths

def choose_apps(app: str, found_apps: list):
    """
    Prompt the user to choose one path for each application pattern, 
    with an option to select 'None'.

    Args:
        app (str): The application name to choose a path for.
        found_apps (list): List of matching paths for the application.

    Returns:
        tuple: A tuple containing the filename without extension and the selected path.
               Returns (None, None) if 'Select None' is chosen.
    """
    print(f"\nChoose a path for '{app}':")
    
    # Add the 'Select None' option
    print("  [0] Select None")
    
    for i, path in enumerate(found_apps):
        print(f"  [{i + 1}] {path}")
        
    while True:
        try:
            choice = int(input(f"Enter your choice (0-{len(found_apps)}): "))
            
            if choice == 0:  # Select None option
                print("No path selected.")
                return None, None
            elif 1 <= choice <= len(found_apps):  # Valid path selection
                selected_path = found_apps[choice - 1]
                print(f"Selected: {selected_path}")
                
                # Extract filename without extension
                filename_with_extension = os.path.basename(selected_path)
                filename = os.path.splitext(filename_with_extension)[0]
                
                return filename, selected_path
            else:
                print("Invalid choice. Please enter a number within the range.")
        except ValueError:
            print("Invalid input. Please enter a valid number.")
            return None, None

def manual_apps():
    """
    Allow manual input of the executable path if no path is chosen 
    and automatically resolve the application name.

    Returns:
        tuple: A tuple containing the resolved application name and selected path.
    """
    print("\nNo path was selected. Please input the executable path manually.")

    # Prompt the user to input the path to the executable
    while True:
        selected_path = input("Enter the full path to the executable (e.g., C:\\Program Files\\Stata18\\StataSE-64.exe): ").strip()
        if os.path.isfile(selected_path) and os.access(selected_path, os.X_OK):  # Validate the path
            break
        else:
            print("Invalid path. Please ensure the file exists and is executable. Try again.")
            return None, None

    # Resolve the application name by extracting the filename without extension
    filename_with_extension = os.path.basename(selected_path)
    filename = os.path.splitext(filename_with_extension)[0]

    return filename, selected_path



# Git Functions:
def git_commit(msg:str=""):
    
    # Set from .env file
    is_installed('git')

    try:
        subprocess.run(["git", "add", "."], check=True)    
        subprocess.run(["git", "commit", "-m", msg], check=True)
    except subprocess.CalledProcessError as e:
        print(f"An error occurred: {e}")

def git_push(msg:str=""):

    def push_all(remote="origin"):
        try:
            # Get the name of the current branch
            current_branch = subprocess.check_output(
                ["git", "branch", "--show-current"],
                text=True
            ).strip()
            
            # Get all local branches
            branches = subprocess.check_output(
                ["git", "branch"],
                text=True
            ).strip().splitlines()
            
            # Clean up branch names
            branches = [branch.strip().replace("* ", "") for branch in branches]
            
            # Filter out the current branch
            branches_to_push = [branch for branch in branches if branch != current_branch]
            
            # Push each branch except the current one
            for branch in branches_to_push:
                subprocess.run(
                    ["git", "push", remote, branch],
                    check=True
                )
            
            print(f"Successfully pushed all branches except '{current_branch}'")
        except subprocess.CalledProcessError as e:
            print(f"Error occurred while pushing branches: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")

    try:
        if os.path.isdir(".datalad"):
            # Set from .env file
            is_installed('git')
            is_installed('datalad')
            is_installed('git-annex')
            is_installed('rclone')
            subprocess.run(["datalad", "save", "-m", msg], check=True)
            push_all()

        elif os.path.isdir(".git"):
            git_commit(msg)
            result = subprocess.run(["git", "branch", "--show-current"], check=True, capture_output=True, text=True)
            branch = result.stdout.strip()  # Remove any extra whitespace or newlin
            if branch:
                subprocess.run(["git", "push", "origin", branch], check=True)
            else:
                subprocess.run(["git", "push", "--all"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"An error occurred: {e}")

def git_user_info(version_control):
    if version_control.lower() in ["git","datalad","dvc"]:    
        git_name = None
        git_email = None
        while not git_name or not git_email:
            git_name = input("Enter your Git user name: ").strip()
            git_email = input("Enter your Git user email: ").strip()
            # Check if inputs are valid
            if not git_name or not git_email:
                print("Both name and email are required.")
        save_to_env(git_name ,'GIT_USER')
        save_to_env(git_email,'GIT_EMAIL')
        return git_name, git_email
    else:
        return None, None
    
def git_repo_user(version_control,repo_name,code_repo):
    if code_repo.lower() in ["github","gitlab"] and version_control.lower() in ["git","datalad","dvc"]: 
        repo_user = None 
        privacy_setting = None
        while not repo_user or not privacy_setting:
            repo_user = input(f"Enter your {code_repo} username:").strip()
            privacy_setting = input("Select the repository visibility (private/public): ").strip().lower()

            if privacy_setting not in ["private", "public"]:
                print("Invalid choice. Defaulting to 'private'.")
                privacy_setting = None

        save_to_env(repo_user,f"{code_repo}_USER")
        save_to_env(privacy_setting,f"{code_repo}_PRIVACY")
        save_to_env(repo_name,f"{code_repo}_REPO") 
        
        return repo_user, privacy_setting
    else:
        return None, None

# Conda Functions:
def setup_conda(install_path:str,repo_name:str, conda_packages:list = [], pip_packages:list = [], env_file:str = None):
    
    install_path = os.path.abspath(install_path)

    if not is_installed('conda','Conda'):
        if not install_miniconda(install_path):
            return False

    if env_file and (env_file.endswith('.yaml') or env_file.endswith('.txt')):
        if env_file.endswith('.txt'):
            env_file = generate_env_yml(repo_name,env_file)
        update_env_yaml(env_file, repo_name, conda_packages)
        command = ['conda', 'env', 'create', '-f', env_file, '--name', repo_name]
        msg = f'Conda environment "{repo_name}" created successfully from {env_file}.'
    else:
        command = ['conda', 'create','--yes', '--name', repo_name, '-c', 'conda-forge']
        command.extend(conda_packages)
        msg = f'Conda environment "{repo_name}" was created successfully. The following packages were installed: conda install = {conda_packages}; pip install = {pip_packages}. '

    python_env, r_env = create_conda_env(repo_name,command,msg)
    pip_install(repo_name, pip_packages)
    export_conda_env(repo_name)
    
    return python_env,r_env

def pip_install(repo_name, pip_packages):
    """
    Activates a Conda environment and installs packages using pip.

    Parameters:
    repo_name (str): Name of the Conda environment to activate.
    pip_packages (list): List of pip packages to install.

    Returns:
    None
    """
    if not pip_packages:
        return

    try:
        # Construct the pip install command
        pip_command = [
            "conda", "run", "-n", repo_name, sys.executable, "-m", "pip", "install"
        ] + pip_packages

        # Execute the pip install command
        subprocess.run(pip_command, check=True)

        print(f"Successfully installed pip packages: {', '.join(pip_packages)} in Conda environment '{repo_name}'.")
    except subprocess.CalledProcessError as e:
        print(f"Error installing pip packages in Conda environment '{repo_name}': {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

def export_conda_env(env_name, output_file='environment.yml'):
    """
    Export the details of a conda environment to a YAML file.
    
    Parameters:
    - env_name: str, name of the conda environment to export.
    - output_file: str, name of the output YAML file. Defaults to 'environment.yml'.
    """
    try:
        # Use subprocess to run the conda export command
        with open(output_file, 'w') as f:
            subprocess.run(['conda', 'env', 'export', '-n', env_name], stdout=f, check=True)
        
        print(f"Conda environment '{env_name}' exported to {output_file}.")
        # Set to .env
        save_to_env(env_name,"CONDA_ENV")

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

def create_conda_env(repo_name,command,msg):
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

        # Run the command and get the Python executable path within the environment
        try:
            python_env = subprocess.check_output(["conda", "run", "-n", repo_name, sys.executable, "-c", "import sys; print(sys.executable)"], text=True).strip()
        except Exception as e:
            python_env = None

        # Run the command and get R home path
        try:
            r_env = subprocess.check_output(["conda", "run", "-n", repo_name, "R", "-e", "cat(R.home())"], text=True).strip()
        except Exception as e:
            r_env = None
        return python_env,r_env
        
    except subprocess.CalledProcessError as e:
        print(f"Failed to create conda environment: {e}")
    except FileNotFoundError:
        print("Conda is not installed or not found in the system path.")
    except Exception as e:
        print(f"An error occurred: {e}")

    return None, None

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
    - Add additional pip packages from `pip_packages` list

    Parameters:
    env_file (str): Path to the existing environment.yml file
    repo_name (str): The new environment name (usually repo name)
    conda_packages (list): List of additional Conda packages to install
    pip_packages (list): List of additional pip packages to install

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

    print(f"Updated {env_file} with new environment name '{repo_name}', added Conda packages, and added pip packages.")



# Other
def get_hardware_info():
    """
    Extract hardware information and save it to a file.
    Works on Windows, Linux, and macOS.
    """
    os_type = platform.system().lower()
    command = ""

    if os_type == "Windows":
        command = "systeminfo"
    elif os_type == "Linux":
        command = "lshw -short"  # Alternative: "dmidecode"
    elif os_type == "Darwin":  # macOS
        command = "system_profiler SPHardwareDataType"
    else:
        print("Unsupported operating system.")
        return

    try:
        # Execute the command and capture the output
        hardware_info = subprocess.check_output(command, shell=True, text=True)

        # Save the hardware information to a file
        with open("hardware_information.txt", "w") as file:
            file.write(hardware_info)

        print("Hardware information saved to hardware_information.txt")

    except subprocess.CalledProcessError as e:
        print(f"Error retrieving hardware information: {e}")


import os
import subprocess
from subprocess import DEVNULL
import sys
import platform
import shutil
from contextlib import contextmanager
from functools import wraps
import pathlib
import getpass
import importlib.metadata


def set_packages(version_control,programming_language):

    if not programming_language or not version_control:
        return []
        
    install_packages = ['python-dotenv','pyyaml','requests','beautifulsoup4','nbformat','setuptools','pathspec','psutil',"py-cpuinfo"]
    if programming_language.lower()  == 'python':
        install_packages.extend(['jupyterlab','pytest'])
    elif programming_language.lower()  == 'stata':
        install_packages.extend(['jupyterlab','stata_setup'])
    elif programming_language.lower()  == 'matlab':
        install_packages.extend(['jupyterlab','jupyter-matlab-proxy'])
    elif programming_language.lower() == 'sas':
        install_packages.extend(['jupyterlab','saspy'])

    if version_control.lower()  == "dvc" and not is_installed('dvc','DVC'):
        install_packages.extend(['dvc[all]'])
    elif version_control.lower()  == "datalad" and not is_installed('datalad','Datalad'):
        install_packages.extend(['datalad-installer','datalad','pyopenssl'])
    
    return install_packages

def install_uv():
    try:
        import uv  # noqa: F401
    except ImportError:
        try:
            print("Installing 'uv' package into current Python environment...")
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "--upgrade", "uv"],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            print("'uv' installed successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Failed to install 'uv' via pip: {e}")

def package_installer(required_libraries: list = None, pip_install: bool = False):
    if not required_libraries:
        return

    try:
        installed_pkgs = {
            dist.metadata["Name"].lower()
            for dist in importlib.metadata.distributions()
        }
    except Exception as e:
        print(f"Error checking installed packages: {e}")
        return

    missing_libraries = []
    for lib in required_libraries:
        norm_name = (
            lib.split("==")[0]
               .split(">=")[0]
               .split("<=")[0]
               .split("~=")[0]
               .strip()
               .lower()
        )
        if norm_name not in installed_pkgs:
            missing_libraries.append(lib)

    if not missing_libraries:
        return

    print(f"Installing missing libraries: {missing_libraries}")

    if not pip_install:
        
        install_uv()

        try:
            subprocess.run(
                [sys.executable, "-m", "uv", "pip", "install"] + missing_libraries,
                check=True,
                stderr=subprocess.DEVNULL
            )
            return
        except subprocess.CalledProcessError:
            print("uv failed. Trying fallback...")

    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install"] + missing_libraries,
            check=True,
            stderr=subprocess.DEVNULL
        )
    except subprocess.CalledProcessError as e:
        print(f"Failed to install with pip: {e}")

def check_path_format(path, project_root=None):
    if not path:
        return path

    if any(sep in path for sep in ["/", "\\", ":"]) and os.path.exists(path):  # ":" for Windows drive letters
        # Set default project root if not provided
        if project_root is None:
            project_root = pathlib.Path(__file__).resolve().parents[2]

        # Resolve both paths fully
        #path = pathlib.Path(path).resolve()
        project_root = pathlib.Path(project_root).resolve()

        #if not path.exists():
        #    return str(path)  # Return as-is if it doesn't exist

        #try:
            # If path is within the project, return as relative (e.g. ./bin/venv/...)
            #relative_path = path.relative_to(project_root)
    
            #path = f"./{relative_path.as_posix()}"
        #except ValueError:
            # Path is outside project, use absolute form
            #path = str(path)

        # Now adjust slashes depending on platform
        system_name = platform.system()
        if system_name == "Windows":
            path = r"{}".format(path.replace("/", "\\"))
            #path = r"{}".format(path.replace("\\", r"\\"))
        else:  # Linux/macOS
            #path = r"{}".format(path.replace("\\", r"\\"))
            path = r"{}".format(path.replace("\\", "/"))

    return path

def load_from_env(env_var: str, env_file: str = ".env"):
    """
    Loads an environment variable's value from a .env file.
    
    Args:
        env_var (str): The name of the environment variable to load.
        env_file (str): The path to the .env file (default is ".env").
        
    Returns:
        str or None: The value of the environment variable if found, otherwise None.
    """

    env_file = pathlib.Path(env_file)
    if not env_file.exists():
        env_file = pathlib.Path(__file__).resolve().parent.parent.parent / env_file.name

    # Attempt to read directly from the .env file
    if env_file.exists():
        env_values = dotenv_values(env_file)
        if env_var.upper() in env_values:
            env_value = env_values[env_var.upper()]
            env_value = check_path_format(env_value) 
            return env_value
    

    # If not found directly, load the .env file into the environment
    load_dotenv(env_file, override=True)
    env_value = os.getenv(env_var.upper())
    if env_value:
        env_value = check_path_format(env_value) 
    else:
        env_value = None 

    return env_value

def save_to_env(env_var: str, env_name: str, env_file: str = ".env"):
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

    env_var = check_path_format(env_var) 

    env_file = pathlib.Path(env_file)
    if not env_file.exists():
        env_file = pathlib.Path(__file__).resolve().parent.parent.parent / env_file.name

    # Read the existing .env file if it exists
    env_lines = []
    if env_file.exists():
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

def exe_to_path(executable: str = None, path: str = None, env_file: str = ".env"):
    """
    Adds the path of an executable binary to the system PATH permanently.
    """

    env_file = pathlib.Path(env_file)
    if not env_file.exists():
        env_file = pathlib.Path(__file__).resolve().parent.parent.parent / env_file.name

    # Ensure it's an absolute path
    path = os.path.abspath(path)

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
            # Immediately apply the change for the current script/session (only works if you're in a shell)
            subprocess.run(f'source {profile_file}', shell=True, executable='/bin/bash')
        
        # Check if executable is found in the specified path
        resolved_path = shutil.which(executable)
        
        if resolved_path:
            resolved_path= os.path.abspath(resolved_path)
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

    env_file = pathlib.Path(env_file)
    if not env_file.exists():
        env_file = pathlib.Path(__file__).resolve().parent.parent.parent / env_file.name

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

package_installer(required_libraries = ['python-dotenv'])

from dotenv import dotenv_values, load_dotenv

pip_packages = set_packages(load_from_env("VERSION_CONTROL",".cookiecutter"),load_from_env("PROGRAMMING_LANGUAGE",".cookiecutter"))
print("dre!!")
print(pip_packages)
package_installer(required_libraries = pip_packages)

@contextmanager
def change_dir(destination):
    cur_dir = os.getcwd()
    destination = str(pathlib.Path(__file__).resolve().parent.parent.parent / pathlib.Path(destination))
    try:
        os.chdir(destination)
        yield
    finally:
        os.chdir(cur_dir)

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


# Setting Options
def git_user_info(version_control):
    if version_control.lower() in ["git", "datalad", "dvc"]:
        # Load defaults
        default_name = load_from_env("AUTHORS", ".cookiecutter")
        default_email = load_from_env("EMAIL", ".cookiecutter")

        git_name = None
        git_email = None

        while not git_name or not git_email:
            # Prompt with defaults
            name_prompt = f"Enter your Git user name [{default_name}]: "
            email_prompt = f"Enter your Git user email [{default_email}]: "

            git_name = input(name_prompt).strip() or default_name
            git_email = input(email_prompt).strip() or default_email

            # Check if inputs are valid
            if not git_name or not git_email:
                print("Both name and email are required.")

        print(f"\nUsing Git user name: {git_name}")
        print(f"Using Git user email: {git_email}\n")

        save_to_env(git_name, 'GIT_USER')
        save_to_env(git_email, 'GIT_EMAIL')
        return git_name, git_email
    else:
        return None, None

def repo_user_info(version_control, repo_name, code_repo):
    valid_repos = ["github", "gitlab", "codeberg"]
    valid_vcs = ["git", "datalad", "dvc"]

    if code_repo.lower() in valid_repos and version_control.lower() in valid_vcs:
        repo_user = None
        privacy_setting = None
        default_setting = "private"
        hostname = None
        default_host = {
            "github": "github.com",
            "gitlab": "gitlab.com",
            "codeberg": "codeberg.org"
        }.get(code_repo.lower())

        while not hostname or not repo_user or not privacy_setting:
            hostname = input(f"Enter {code_repo} hostname [{default_host}]: ").strip() or default_host
            repo_user = input(f"Enter your {code_repo} username: ").strip()
            privacy_setting = input(f"Select the repository visibility (private/public) [{default_setting}]: ").strip().lower() or default_setting

            if privacy_setting not in ["private", "public"]:
                print("Invalid choice. Defaulting to 'private'.")
                privacy_setting = None

        # Assign keys based on repository
        if code_repo.lower() == "github":
            token_env_key = "GITHUB_TOKEN"
            user_env_key = "GITHUB_USER"
            host_env_key = "GITHUB_HOSTNAME"
            repo_env_key = "GITHUB_REPO"
            privacy_env_key = "GITHUB_PRIVACY"
        elif code_repo.lower() == "gitlab":
            token_env_key = "GITLAB_TOKEN"
            user_env_key = "GITLAB_USER"
            host_env_key = "GITLAB_HOSTNAME"
            repo_env_key = "GITLAB_REPO"
            privacy_env_key = "GITLAB_PRIVACY"
        elif code_repo.lower() == "codeberg":
            token_env_key = "CODEBERG_TOKEN"
            user_env_key = "CODEBERG_USER"
            host_env_key = "CODEBERG_HOSTNAME"
            repo_env_key = "CODEBERG_REPO"
            privacy_env_key = "CODEBERG_PRIVACY"

        # Token retrieval
        token = load_from_env(token_env_key)
        if not token:
            while not token:
                token = getpass.getpass(f"Enter {code_repo} token: ").strip()

        # Save credentials and info
        save_to_env(repo_user, user_env_key)
        save_to_env(privacy_setting, privacy_env_key)
        save_to_env(repo_name, repo_env_key)
        save_to_env(token, token_env_key)
        save_to_env(hostname, host_env_key)

        return repo_user, privacy_setting, token, hostname
    else:
        return None, None, None, None

def remote_user_info(remote_name,repo_name):
    """Prompt for remote login credentials and base folder path."""

    if remote_name.lower() == "deic storage":
        
        email = load_from_env("DEIC_EMAIL")
        password = load_from_env("DEIC_PASS")
        base_folder = load_from_env("DEIC_BASE")
        if email and password and base_folder:
            return email, password, base_folder
        
        # Handle base folder input (default from input value or fallback to home dir)
        default_email = load_from_env("EMAIL", ".cookiecutter")
        default_base = 'RClone_backup/' + repo_name
        base_folder = input(f"Enter base folder for {remote_name} [{default_base}]: ").strip() or default_base

        email = password = None

        while not email or not password:
            email = input(f"Please enter email to Deic Storage [{default_email}]: ").strip() or default_email
            password = getpass.getpass("Please enter password to Deic Storage: ").strip()

            if not email or not password:
                print("Both email and password are required.\n")

        print(f"\nUsing email: {email}")
        print(f"Using base folder: {base_folder}\n")

        save_to_env(email,"DEIC_EMAIL")
        save_to_env(password,"DEIC_PASS")
        save_to_env(base_folder,"DEIC_BASE")

        return email, password, base_folder
    elif remote_name.lower() != "none":
        # Handle base folder input (default from input value or fallback to home dir)
        default_base = 'RClone_backup/' + repo_name
        base_folder = input(f"Enter base folder for {remote_name} [{default_base}]: ").strip() or default_base
        # Add other remote handlers here if needed
        return None, None, base_folder
    else:
        return None, None, None
  

# Setting programming language 
def set_programming_language(programming_language):

    def search_apps(app: str):
        """
        Search for executables matching partial app names in the system's PATH.

        Args:
            app (str): Partial name of the application to search for.

        Returns:
            list: A list of paths matching the executable pattern.
        """
        found_paths = []
        system_paths = os.environ["PATH"].split(os.pathsep)  # Split PATH into directories

        # Check if the app is a single letter
        is_single_letter_app = len(app) == 1

        for directory in system_paths:
            if os.path.isdir(directory):  # Check if the PATH directory exists
                try:
                    for file in os.listdir(directory):
                        # Extract the filename without extension
                        filename_without_ext = os.path.splitext(os.path.basename(file))[0].lower()

                        # Match exactly if the app is a single letter, or partially if it's longer
                        if is_single_letter_app:
                            if filename_without_ext == app.lower():
                                full_path = os.path.join(directory, file)
                                if os.access(full_path, os.X_OK):  # Check if file is executable
                                    found_paths.append(full_path)
                        else:
                            if app.lower() in filename_without_ext:
                                full_path = os.path.join(directory, file)
                                if os.access(full_path, os.X_OK):  # Check if file is executable
                                    found_paths.append(full_path)

                except PermissionError:
                    continue  # Skip directories with permission issues

        if not found_paths:
            print(f"No executables found for app '{app}'.")

        found_paths = list(set(found_paths))

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
        
        if len(found_apps) == 0:
            return None, None
        
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
        and automatically resolve the application name. Re-prompts if the path 
        contains single backslashes.

        Returns:
            tuple: A tuple containing the resolved application name and selected path.
        """
        print("\nNo path was selected. Please input the executable path manually.")

        msg = "Enter the full path to the executable e.g. 'C:/Program Files/Stata18/StataSE-64.exe':"
        # Prompt the user to input the path to the executable
        while True:
            selected_path = input(msg).strip()
            selected_path = selected_path.replace("'", "").replace('"', '')     
            selected_path = check_path_format(selected_path)
    
            if os.path.isfile(selected_path) and os.access(selected_path, os.X_OK):  # Validate the path
                break  # Exit loop if the file exists and is executable
            else:
                answer = ask_yes_no("Invalid path. Do you want to input a new path? (yes/no)")
                
                if answer:
                    msg = "Enter the full path to the executable with forward slashes('/') e.g. 'C:/Program Files/Stata18/StataSE-64.exe':"
                    continue  # Re-prompt the user if single backslashes are detected   
                else:
                    return None, None

        # Resolve the application name by extracting the filename without extension
        filename_with_extension = os.path.basename(selected_path)
        filename = os.path.splitext(filename_with_extension)[0]

        return filename, selected_path

    found_apps = search_apps(programming_language)
    _, selected_path = choose_apps(programming_language,found_apps)

    if not selected_path: 
        _, selected_path =manual_apps()

    if  selected_path:    
        #save_to_env(os.path.dirname(selected_path),programming_language.upper())
        save_to_env(selected_path,programming_language.upper())
        save_to_env(programming_language.lower(),"PROGRAMMING_LANGUAGE",".cookiecutter")

    return programming_language

def get_version(programming_language):
    
    if programming_language not in ["python","pip","uv"]:
        exe_path = load_from_env(programming_language)
        exe_path  = check_path_format(exe_path)
        if not exe_path:
            return "Unknown"
    
    if programming_language.lower() == "python":
        version  = f"{subprocess.check_output([sys.executable, '--version']).decode().strip()}"
    elif programming_language.lower() == "r":
        if not exe_path:
            return "R"
        version = subprocess.run([exe_path, '-e', 'cat(paste(R.version$version))'], capture_output=True, text=True)
        version = version.stdout[0:17].strip()
    elif programming_language.lower() == "matlab":
        if not exe_path:
            return "Matlab"
        version = subprocess.run([exe_path, "-batch", "disp(version)"], capture_output=True, text=True)
        version = f"Matlab {version.stdout.strip()}"
    elif programming_language.lower() == "stata":
        if not exe_path:
            return "Stata"
        # Extract edition based on executable name
        edition = "SE" if "SE" in exe_path else ("MP" if "MP" in exe_path else "IC")
        # Extract version from the folder name (e.g., Stata18 -> 18)
        version = os.path.basename(os.path.dirname(exe_path)).replace('Stata', '')
        # Format the output as Stata version and edition
        version = f"Stata {version} {edition}"
    elif programming_language.lower() == "sas": # FIX ME
        if not exe_path:
            return "Sas"
        version = subprocess.run([exe_path, "-version"], capture_output=True, text=True)
        version =version.stdout.strip()  # Returns version info
    elif programming_language.lower() == "pip":
        try:
            version = subprocess.check_output(["pip", "--version"], text=True)
            version = " ".join(version.split()[:2])    
        except subprocess.CalledProcessError as e:
            return "pip"
    elif programming_language.lower() == "uv":
        try:
            version = subprocess.check_output(["uv", "--version"], text=True)
            version = version.strip()  # Returns version info       
        except subprocess.CalledProcessError as e:
            return "uv" 
    elif programming_language.lower() == "conda":
        if not exe_path:
            return "conda"   
        version = subprocess.check_output(["conda", "--version"], text=True)
        version = version.strip()  # e.g., "conda 24.3.0"    
    return version

def run_script(programming_language, script_command=None):
    """
    Runs a script or fetches version info for different programming languages.
    
    Args:
        programming_language (str): Programming language name (e.g., 'python', 'r', etc.)
        script_command (str, optional): Script/command to execute. Optional for languages like Stata.
    
    Returns:
        str: Output or version string.
    """
    programming_language = programming_language.lower()

    if programming_language != "python":
        exe_path = load_from_env(programming_language)
        exe_path = check_path_format(exe_path)
        if not exe_path:
            return "Unknown executable path"

    try:
        if programming_language == "python":
            cmd = sys.executable + " -c " + script_command
            #cmd = [sys.executable, "-c"]
            #cmd.extend(script_command)
            
            result = subprocess.run(
                cmd,
                capture_output=True, text=True, check=True
            )
            return result.stdout.strip()

        elif programming_language == "r":
            cmd = exe_path + " --vanilla" + script_command
            #cmd = [exe_path,"--vanilla"]
            #cmd.extend(script_command)
            result = subprocess.run(
                cmd,
                capture_output=True, text=True, check=True
            )
            return result.stdout.strip()
        
        elif programming_language == "matlab":
            cmd = exe_path + " -batch " + script_command
            print(cmd)
            result = subprocess.run(
                cmd,
                capture_output=True, text=True, check=True
            )
            return result.stdout.strip()

        elif programming_language == "stata":
            # For Stata, run the executable with --version (or equivalent) to print version
            cmd = exe_path +  " -b " + script_command
            print(cmd)
            result = subprocess.run(
                cmd,
                capture_output=True, text=True
            )
            return result.stdout.strip() if result.stdout else "Stata version information not captured."

        elif programming_language == "sas":
            cmd = exe_path  + " -SYSIN " + script_command
            #cmd = [exe_path, "-SYSIN"]
            #cmd.extend(script_command)
            result = subprocess.run(
                cmd,
                capture_output=True, text=True, check=True
            )
            return result.stdout.strip()

        else:
            return f"Language {programming_language} not supported."

    except subprocess.CalledProcessError as e:
        return f"Error running script: {e.stderr.strip()}"

def make_safe_path(path: str, language: str = "python") -> str:
    """
    Convert a file path to a language-safe format.
    
    Args:
        path (str): The input file path.
        language (str): One of 'python', 'r', 'matlab', 'stata'.
    
    Returns:
        str: Formatted path string suitable for the specified language.
    """
    path = os.path.abspath(path)
    path_fixed = path.replace("\\", "/")  # Normalize slashes for all languages

    language = language.lower()
    if language == "python":
        return path_fixed  # Use as-is, Python handles forward slashes fine
    elif language == "r":
        return f"\"{path_fixed}\"" 
    elif language == "matlab":
        return f"'{path_fixed}'"  # Wrap in single quotes
    elif language == "stata":
        return f'"{path_fixed}"'  # Wrap in double quotes (for use in do-files)
    else:
        raise ValueError(f"Unsupported language: {language}")

def set_program_path(programming_language):

    if programming_language.lower() not in ["python","none"]:
        exe_path = load_from_env(programming_language.upper())
        
        if not exe_path:
            exe_path = shutil.which(programming_language.lower())
        
        if exe_path:
            save_to_env(check_path_format(exe_path), programming_language.upper())
            save_to_env(get_version(programming_language), f"{programming_language.upper()}_VERSION",".cookiecutter")

    if not load_from_env("PYTHON"):
        save_to_env(sys.executable, "PYTHON")
        save_to_env(get_version("python"), "PYTHON_VERSION",".cookiecutter")

#Check software
def ensure_correct_kernel(func):
    """Decorator to ensure the function runs with the correct Python kernel."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        python_kernel = load_from_env("PYTHON")  # Load the desired kernel path from the environment
        
        # If no specific kernel is set, just run the function normally
        if not python_kernel:
            return func(*args, **kwargs)
        
        os_type = platform.system().lower()
        if os_type == "windows":
            py_exe = "python.exe"
        elif os_type == "darwin" or os_type == "linux":
            py_exe = "python"

        # If the kernel path doesn't contain "python.exe", append it
        if not python_kernel.endswith(py_exe):
            python_kernel = os.path.join(python_kernel, py_exe)

        # Get the current executable and its base folder
        current_executable = sys.executable
        current_base = os.path.dirname(current_executable)
        kernel_base = os.path.dirname(python_kernel)

        # If the current Python executable does not match the required kernel, restart
        if current_executable != python_kernel and current_base != kernel_base:
            print(f"Restarting with the correct Python kernel: {python_kernel}")

            # Re-run the script with the correct Python interpreter
            script_path = os.path.abspath(__file__)
            subprocess.run([python_kernel, script_path] + sys.argv[1:], check=True)
            sys.exit()  # Terminate the current process after restarting

        # If the kernel is correct, execute the function normally
        return func(*args, **kwargs)

    return wrapper

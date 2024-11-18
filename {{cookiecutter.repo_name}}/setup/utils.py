import os
import subprocess
import sys
import platform

import importlib
import shutil

required_libraries = ['python-dotenv'] 
for lib in required_libraries:
    try:
        importlib.import_module(lib)
    except ImportError:
        print(f"Installing {lib}...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', lib])


from dotenv import load_dotenv

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

def load_from_env(executable: str, env_file=".env"):
    """
    Tries to load the environment variable for the given executable from the .env file.
    If the variable exists and points to a valid binary path, adds it to the system PATH.

    Args:
        executable (str): The name of the executable.
        env_file (str): The path to the .env file. Defaults to '.env'.
    """
    # Load the .env file
    load_dotenv(env_file)

    # Get the environment variable for the executable (uppercase)
    env_var = os.getenv(executable.upper())
    if not env_var:
        return False

    # Construct the binary path
    bin_path = os.path.join(env_var, "bin", executable)
    if os.path.exists(bin_path):
        return add_to_path(executable, os.path.dirname(bin_path))
    else:
        return False

def add_to_path(executable: str = None,bin_path: str = None):
        """
        Adds the path of an executalbe binary to the system PATH permanently.
        """
        os_type = platform.system().lower() 
        if os.path.exists(bin_path):
                    # Add to current session PATH
            os.environ["PATH"] += os.pathsep + bin_path

            if os_type == "windows":
                # Use setx to set the environment variable permanently in Windows
                subprocess.run(["setx", "PATH", f"{bin_path};%PATH%"], check=True)
                return True
            else:
                # On macOS/Linux, you can add the path to the shell profile file
                profile_file = os.path.expanduser("~/.bashrc")  # or ~/.zshrc depending on shell
                with open(profile_file, "a") as file:
                    file.write(f'\nexport PATH="{bin_path}:$PATH"')
                print(f"Added {bin_path} to PATH. Restart the terminal or source {profile_file} to apply.")
                return True
        else:
            print(f"{executable} binary not found in {bin_path}, unable to add to PATH.")
            return False
        
def add_to_env(executable: str = None,env_file=".env"):
    # Check if .env file exists
    if not os.path.exists(env_file):
        print(f"{env_file} does not exist. Creating a new one.")
    
    # Write the credentials to the .env file
    with open(env_file, 'a') as file:  
        file.write(f"{executable.upper()}={shutil.which(executable)}\n")

def is_installed(executable: str = None, name: str = None):
    # Check if both executable and name are provided as strings
    if not isinstance(executable, str) or not isinstance(name, str):
        raise ValueError("Both 'executable' and 'name' must be strings.")
    
    if not load_from_env(executable):
        # Check if the executable is on the PATH
        path = shutil.which(executable)
        if path:
            add_to_env(executable)
            return True
        else: 
            print(f"{name} is not on Path")
            return False
  

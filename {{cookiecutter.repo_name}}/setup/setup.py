import os
import subprocess
import sys
import platform
import pathlib

# Change to project root directory
project_root = pathlib.Path(__file__).resolve().parent.parent
os.chdir(project_root)

# Add the directory to sys.path
script_dir = "setup"
if script_dir not in sys.path:
    sys.path.append(script_dir)

setup_bash_script = "setup/setup.sh"
setup_powershell_script = "setup/setup.ps1"

def run_bash_script(script_path):
    try:
        # Make sure the script is executable
        os.chmod(script_path, 0o755)

        # Run the script with the additional paths as arguments
        subprocess.check_call([script_path])  # Pass repo_name and paths to the script
        print(f"Script {script_path} executed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while executing the script: {e}")

def run_powershell_script(script_path):
    try:
        # Prepare the command to execute the PowerShell script with arguments
        command = [
            "powershell", "-ExecutionPolicy", "Bypass", "-File", script_path
        ]

        # Run the PowerShell script with the specified arguments
        subprocess.check_call(command)
        print(f"Script {script_path} executed successfully.")
    
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while executing the script: {e}")

os_type = platform.system().lower()

if os_type == "windows":
    run_powershell_script(setup_powershell_script)
elif os_type == "darwin" or os_type == "linux":
    run_bash_script(setup_bash_script)
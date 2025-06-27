import subprocess
import pathlib
import sys
import platform


def run_in_venv():
    if platform.system() == "Windows":
        cmd = r".venv\Scripts\activate.bat && python setup\project_setup.py"
        subprocess.run(cmd, shell=True)  # Uses cmd.exe by default
    else:
        cmd = "source .venv/bin/activate && python setup/project_setup.py"
        subprocess.run(cmd, shell=True, executable="/bin/bash")  # Uses bash

def install_uv():
    """Ensure 'uv' is installed and usable."""
    try:
        # Check if uv is already installed
        subprocess.run(["uv", "--version"], check=True, stdout=subprocess.DEVNULL)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️ 'uv' not found. Attempting to install it via pip...")
        try:
            subprocess.run(["pip", "install", "--upgrade", "uv"],check=True)
            # Verify installation
            subprocess.run(["uv", "--version"], check=True, stdout=subprocess.DEVNULL)
            return True
        except subprocess.CalledProcessError:
            return False

def create_with_uv():
    """Create virtual environment using uv silently."""
    subprocess.run(["uv", "venv"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["uv", "lock"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(
        ["uv", "add", "--upgrade", "uv", "pip", "setuptools", "wheel"],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    # This one shows output
    subprocess.run(["uv", "run", "setup/project_setup.py"], check=True)

    
def main():
    env_path = pathlib.Path(".venv")  # Now it's a Path object

    # Create venv only if it doesn't exist
    if not env_path.exists() and install_uv():
            try:
                create_with_uv()
            except subprocess.CalledProcessError as e:
                print("hello1")
                subprocess.run(["python", "setup/project_setup.py"])
    else:
        print("hello2")
        subprocess.run(["python", "setup/project_setup.py"])
   
if __name__ == "__main__":
    main()

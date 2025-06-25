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
            subprocess.run([sys.executable, "pip", "install", "--upgrade", "uv"],check=True)
            #subprocess.run([sys.executable, "-m", "pip", "install", "uv"], check=True)
            # Verify installation
            subprocess.run(["uv", "--version"], check=True, stdout=subprocess.DEVNULL)
            return True
        except subprocess.CalledProcessError:
            return False

def create_with_uv():
    """Create virtual environment using uv."""
    #subprocess.run(["uv", "init"], check=True)
    subprocess.run(["uv", "venv"], check=True)
    subprocess.run(["uv", "lock"], check=True)
    subprocess.run(["uv", "add","uv"], check=True)
    subprocess.run(["uv", "run","setup/project_setup.py"], check=True)
    
def main():
    env_path = pathlib.Path(".venv")  # Now it's a Path object

    # Create venv only if it doesn't exist
    if not env_path.exists() and install_uv():
            try:
                create_with_uv()
                #run_in_venv()
            except subprocess.CalledProcessError as e:
                subprocess.run(["python", "setup/project_setup.py"])
    else:
        subprocess.run(["python", "setup/project_setup.py"])
   
if __name__ == "__main__":
    main()

import subprocess
import pathlib
import sys

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
            #subprocess.run([sys.executable, "-m", "pip", "install", "uv"], check=True)
            # Verify installation
            subprocess.run(["uv", "--version"], check=True, stdout=subprocess.DEVNULL)
            return True
        except subprocess.CalledProcessError:
            return False
def create_venv_with_uv(env_path):
    """Create virtual environment using uv."""
    subprocess.run(["uv", "init"], check=True)
    subprocess.run(["uv", "venv"], check=True)
    subprocess.run(["uv", "lock"], check=True)
    return env_path / ("Scripts" if sys.platform.startswith("win") else "bin") / "python"

def main():
    env_path = pathlib.Path(".venv")  # Now it's a Path object

    # Create venv only if it doesn't exist
    if not env_path.exists() and install_uv():
            try:
                python_path = create_venv_with_uv(env_path)
                subprocess.run([str(python_path), "setup/project_setup.py"])
            except subprocess.CalledProcessError as e:
                subprocess.run(["python", "setup/project_setup.py"])
    else:
        subprocess.run(["python", "setup/project_setup.py"])
   
if __name__ == "__main__":
    main()

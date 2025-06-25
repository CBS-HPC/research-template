import subprocess
import pathlib
import sys

def install_uv():
    """Check if 'uv' is installed and usable."""
    try:
        subprocess.run([sys.executable, "-m", "uv", "--version"], check=True, stdout=subprocess.DEVNULL)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def create_venv_with_uv(env_path):
    """Create virtual environment using uv."""
    subprocess.run([sys.executable, "-m", "uv", "venv", str(env_path)], check=True)
    return env_path / ("Scripts" if sys.platform.startswith("win") else "bin") / "python"

def main():
    env_path = ".venv"

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

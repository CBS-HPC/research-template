import subprocess
import pathlib
import sys
import platform

def run_in_venv():
    if platform.system() == "Windows":
        cmd = r".venv\Scripts\activate.bat && python setup\project_setup.py"
        subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        cmd = "source .venv/bin/activate && python setup/project_setup.py"
        subprocess.run(cmd, shell=True, executable="/bin/bash", stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def install_uv():
    """Ensure 'uv' is installed and usable."""
    try:
        subprocess.run(["uv", "--version"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "uv"],
                           check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["uv", "--version"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except subprocess.CalledProcessError:
            return False

def create_with_uv():
    """Create virtual environment using uv silently."""
  
    try:
        subprocess.run(["uv", "venv"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["uv", "lock"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)    
        subprocess.run(
            ["uv", "add","uv", "pip", "setuptools", "wheel"],
            #["uv", "add", "--upgrade", "uv", "pip", "setuptools", "wheel"],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError:
        try:
            subprocess.run(
                ["uv", "add", "uv", "pip", "setuptools", "wheel", "--link-mode=copy"],
                #["uv", "add", "--upgrade", "uv", "pip", "setuptools", "wheel", "--link-mode=copy"],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except subprocess.CalledProcessError:
            # fallback to pip install
            subprocess.run(
                [sys.executable, "-m", "pip", "install","uv", "pip", "setuptools", "wheel"],
                #[sys.executable, "-m", "pip", "install", "--upgrade", "uv", "pip", "setuptools", "wheel"],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
    # Run the setup script and show output (so user sees progress/errors here)
    #subprocess.run(["uv", "run", "setup/project_setup.py"], check=True)
    subprocess.run([sys.executable, "setup/project_setup.py"], check=True)

def main():
    env_path = pathlib.Path(".venv")
    if not env_path.exists():
        if install_uv():
            create_with_uv()
            return
    subprocess.run([sys.executable, "setup/project_setup.py"], check=True)
    return
if __name__ == "__main__":
    main()

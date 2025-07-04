import subprocess
import pathlib
import sys
import platform
import os

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
            subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "uv"],
                           check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["uv", "--version"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except subprocess.CalledProcessError:
            return False

def create_with_uv():
    """Create virtual environment using uv with UV_LINK_MODE=copy to avoid hardlink errors."""

    env = os.environ.copy()
    env["UV_LINK_MODE"] = "copy"

    # Run uv commands with environment forcing copy mode
    subprocess.run(["uv", "venv"], check=True, env=env)
    subprocess.run(["uv", "lock"], check=True, env=env)

    try:
        subprocess.run(
            ["uv", "add", "--upgrade", "uv", "pip", "setuptools", "wheel", "python-dotenv"],
            check=True,
            env=env,
            # Uncomment to silence output:
            # stdout=subprocess.DEVNULL,
            # stderr=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError:
        print("Failed to add packages with uv add --upgrade (even with link-mode=copy).")
        raise

    # Run the setup script and show output so user sees progress/errors
    subprocess.run(["uv", "run", "setup/project_setup.py"], check=True, env=env)


def create_with_uv_old():
    
    """Create virtual environment using uv silently."""

    #subprocess.run(["uv", "venv"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    #subprocess.run(["uv", "lock"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["uv", "venv"], check=True)
    subprocess.run(["uv", "lock"], check=True)

    try:  
        subprocess.run(
            ["uv", "add", "--upgrade","uv", "pip", "setuptools", "wheel", "python-dotenv"],
            check=True,
            #stdout=subprocess.DEVNULL,
            #stderr=subprocess.DEVNULL,
        )

    except subprocess.CalledProcessError:
            subprocess.run(
            ["uv", "add", "--upgrade", "uv", "pip", "setuptools", "wheel", "python-dotenv", "--link-mode=copy"],
            check=True,
            #stdout=subprocess.DEVNULL,
            #stderr=subprocess.DEVNULL,
        )

    # Run the setup script and show output (so user sees progress/errors here)
    subprocess.run(["uv", "run", "setup/project_setup.py"], check=True)

def create_with_pip():
    subprocess.run(
                [sys.executable, "-m", "pip", "--upgrade", "install", "uv", "setuptools", "wheel", "python-dotenv"],

                check=True,
                #stdout=subprocess.DEVNULL,
                #stderr=subprocess.DEVNULL,
            )    
    subprocess.run([sys.executable, "setup/project_setup.py"], check=True)

def main():
    env_path = pathlib.Path(".venv")
    if not env_path.exists():
        if install_uv():
            create_with_uv()
            return
    
    create_with_pip()
    return
if __name__ == "__main__":
    main()

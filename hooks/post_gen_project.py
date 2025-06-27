import subprocess
import pathlib
import sys
import platform
import shutil


def run_in_venv():
    if platform.system() == "Windows":
        cmd = r".venv\Scripts\activate.bat && python setup\project_setup.py"
        subprocess.run(cmd, shell=True)
    else:
        cmd = "source .venv/bin/activate && python setup/project_setup.py"
        subprocess.run(cmd, shell=True, executable="/bin/bash")


def install_uv():
    """Ensure 'uv' is installed and usable."""
    try:
        subprocess.run(["uv", "--version"], check=True, stdout=subprocess.DEVNULL)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️  'uv' not found. Attempting to install it via pip...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "uv"], check=True)
            subprocess.run(["uv", "--version"], check=True, stdout=subprocess.DEVNULL)
            return True
        except subprocess.CalledProcessError:
            print("❌ Failed to install 'uv'.")
            return False


def create_with_uv():
    """Create virtual environment using uv."""
    try:
        subprocess.run(["uv", "venv"], check=True)
        subprocess.run(["uv", "lock"], check=True)
        
        try:
            subprocess.run(
                ["uv", "add", "--upgrade", "uv", "pip", "setuptools", "wheel"],
                check=True,
            )
        except subprocess.CalledProcessError:
            # Retry with link-mode=copy
            try:
                subprocess.run(
                    ["uv", "add", "--upgrade", "uv", "pip", "setuptools", "wheel", "--link-mode=copy"],
                    check=True,
                )
            except subprocess.CalledProcessError:
                subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "uv", "pip", "setuptools", "wheel"], check=True)

        subprocess.run(["uv", "run", "setup/project_setup.py"], check=True)

    except subprocess.CalledProcessError as e:
        print("❌ Error during uv-based environment setup:", e)
        raise


def main():
    env_path = pathlib.Path(".venv")

    if not env_path.exists():
        if install_uv():
            try:
                create_with_uv()
            except subprocess.CalledProcessError:
                print("⚠️  Falling back to plain Python execution.")
                subprocess.run([sys.executable, "setup/project_setup.py"], check=True)
        else:
            print("⚠️  Could not use uv. Falling back.")
            subprocess.run([sys.executable, "setup/project_setup.py"], check=True)
    else:
        # .venv already exists — assume it's usable
        print("✅ Virtual environment already exists.")
        subprocess.run([sys.executable, "setup/project_setup.py"], check=True)


if __name__ == "__main__":
    main()

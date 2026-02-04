import subprocess
import pathlib
import sys
import platform
import os
import shutil

if sys.version_info < (3, 11):
    TOML_VERSION = "toml"
else:
    TOML_VERSION = "tomli-w"


def run_in_venv():
    if platform.system() == "Windows":
        cmd = r".venv\Scripts\activate.bat && python setup\project_setup.py"
        subprocess.run(
            cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
    else:
        cmd = "source .venv/bin/activate && python setup/project_setup.py"
        subprocess.run(
            cmd,
            shell=True,
            executable="/bin/bash",
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )


def install_uv():
    """Ensure 'uv' is installed and usable."""
    try:
        subprocess.run(
            ["uv", "--version"],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "--upgrade", "uv"],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            subprocess.run(
                ["uv", "--version"],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return True
        except subprocess.CalledProcessError:
            return False


def create_with_uv():
    """Create virtual environment using uv with UV_LINK_MODE=copy to avoid hardlink errors,
    then run setup with the interpreter from .venv (not `uv run`)."""

    env = os.environ.copy()
    env["UV_LINK_MODE"] = "copy"

    # Create venv and lock deps with uv
    subprocess.run(
        ["uv", "venv"],
        check=True,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        subprocess.run(
            ["uv", "lock"],
            check=True,
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError:
        print("uv lock failed; continuing without lock.")


    # Use the venv's python instead of `uv run` as it corrupts runn_setup.ps1/.sh
    python_exe = (
        os.path.join(".venv", "Scripts", "python.exe")
        if os.name == "nt"
        else os.path.join(".venv", "bin", "python")
    )
    if not os.path.exists(python_exe):
        raise FileNotFoundError(
            f"Python interpreter not found at {python_exe}. Did 'uv venv' succeed?"
        )

    # Ensure uv is installed inside the created venv
    subprocess.run(
        [python_exe, "-m", "ensurepip", "--upgrade"],
        check=False,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    subprocess.run(
        [python_exe, "-m", "pip", "install", "--upgrade", "uv", "pip", "setuptools", "wheel"],
        check=False,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    try:
        subprocess.run(
            [
                python_exe,
                "-m",
                "uv",
                "pip",
                "install",
                "--upgrade",
                "python-dotenv",
                "pathspec",
                "pyyaml",
                TOML_VERSION,
            ],
            check=True,
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError:
        print("Failed to add packages with uv pip install (even with link-mode=copy).")
        raise

    # Run the setup script and show output so user sees progress/errors
    subprocess.run([python_exe, "setup/project_setup.py"], check=True, env=env)


def create_with_pip():
    # Always bootstrap uv and then use the uv-based path
    subprocess.run(
        [sys.executable, "-m", "ensurepip", "--upgrade"],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "--upgrade", "uv"],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    create_with_uv()


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

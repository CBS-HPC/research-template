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

REPOKIT_DIR = pathlib.Path("setup") / "repokit"
REPOKIT_COMMON_PATH = (
    REPOKIT_DIR / "external" / "repokit-common" / "src" / "repokit_common"
)
REPOKIT_GIT_URL = "https://github.com/CBS-HPC/repokit.git"


def ensure_repokit_sources(env: dict | None = None) -> None:
    """
    Ensure repokit + repokit-common sources exist for project_setup.py imports.
    This handles cases where nested submodules were not initialized by cookiecutter.
    """
    if REPOKIT_COMMON_PATH.exists():
        return

    if not shutil.which("git"):
        print("Git not found; cannot initialize repokit submodules.")
        return

    # If setup/repokit exists but is empty, replace with a fresh clone
    if REPOKIT_DIR.exists():
        try:
            if not any(REPOKIT_DIR.iterdir()):
                shutil.rmtree(REPOKIT_DIR, ignore_errors=True)
        except OSError:
            pass

    if not REPOKIT_DIR.exists():
        subprocess.run(
            ["git", "clone", REPOKIT_GIT_URL, str(REPOKIT_DIR)],
            check=False,
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    # Ensure nested submodules (repokit-common/backup/dmp)
    if REPOKIT_DIR.exists():
        subprocess.run(
            ["git", "-C", str(REPOKIT_DIR), "submodule", "update", "--init", "--recursive"],
            check=False,
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )


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
    )
    try:
        subprocess.run(
            ["uv", "lock"],
            check=True,
            env=env,
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
    )
    subprocess.run(
        [python_exe, "-m", "pip", "install", "--upgrade", "uv", "pip", "setuptools", "wheel"],
        check=False,
        env=env,
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
    #project_root = pathlib.Path(__file__).resolve().parent.parent
    #print(f"PROJECT_DIR: {project_root}")
    #os.chdir(project_root)
    #ensure_repokit_sources()
    #os.chdir(project_root)
    #ensure_repokit_sources()
    env_path = pathlib.Path(".venv")
    if not env_path.exists():
        if install_uv():
            create_with_uv()
            return

    create_with_pip()
    return


if __name__ == "__main__":
    main()

import os
import subprocess
from subprocess import DEVNULL
import re
import sys
import platform
import shutil
from contextlib import contextmanager
from functools import wraps
import pathlib
import getpass
#import importlib
import importlib.metadata
import importlib.util
from typing import List, Optional


def project_root() -> pathlib.Path:
    return pathlib.Path(__file__).resolve().parent.parent.parent

# Convenience constant + helper
PROJECT_ROOT = project_root()

def from_root(*parts: str | os.PathLike) -> pathlib.Path:
    """Join paths relative to the detected project root."""
    return PROJECT_ROOT.joinpath(*map(str, parts))


def split_multi(val: Optional[str]) -> List[str]:
    if not val or not isinstance(val, str):
        return None
    raw = [p.strip() for p in val.replace(";", ",").split(",")]
    return [p for p in raw if p]

def ask_yes_no(question):
    """
    Prompt the user with a yes/no question and validate the input.

    Args:
        question (str): The question to display to the user.

    Returns:
        bool: True if the user confirms (yes/y), False if the user declines (no/n).
    """
    while True:
        response = input(question).strip().lower()
        if response in {"yes", "y"}:
            return True
        elif response in {"no", "n"}:
            return False
        else:
            print("Invalid response. Please answer with 'yes' or 'no'.")

def create_uv_project():
    """
    Runs `uv lock` if pyproject.toml exists, otherwise runs `uv init`.
    Skips both if uv.lock already exists.
    """
    project_path = PROJECT_ROOT
    pyproject_path = project_path / "pyproject.toml"
    uv_lock_path = project_path / "uv.lock"
    
    env = os.environ.copy()
    env["UV_LINK_MODE"] = "copy"

    if uv_lock_path.exists():
        print("✔️  uv.lock already exists — skipping `uv init` or `uv lock`.")
        return

    if not install_uv():
        print("❌ 'uv' is not installed or not available in PATH.")
        return

    try:
        if pyproject_path.exists():
            print("✅ pyproject.toml found — running `uv lock`...")
            subprocess.run(["uv", "lock"], check=True,env=env,cwd=project_path)
        else:
            print("No pyproject.toml found — running `uv init`...")
            subprocess.run(["uv", "init"], check=True,env=env,cwd=project_path)
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed: {e}")

def set_packages(version_control,programming_language):

    if not programming_language or not version_control:
        return []

    install_packages = ['python-dotenv','pyyaml','requests','beautifulsoup4','nbformat','setuptools','pathspec','psutil','py-cpuinfo','jinja2','streamlit','dirhash']

    # Add toml package if Python version < 3.11
    if sys.version_info < (3, 11):
        install_packages.append('toml')
    else:
        install_packages.append('tomli-w')
     
    if programming_language.lower()  == 'python':
        install_packages.extend(['jupyterlab','pytest'])
    elif programming_language.lower()  == 'stata':
        install_packages.extend(['jupyterlab','stata_setup'])
    elif programming_language.lower()  == 'matlab':
        install_packages.extend(['jupyterlab','jupyter-matlab-proxy'])
    elif programming_language.lower() == 'sas':
        install_packages.extend(['jupyterlab','saspy'])

    if version_control.lower()  == "dvc" and not is_installed('dvc','DVC'):
        install_packages.extend(['dvc[all]'])
    elif version_control.lower()  == "datalad" and not is_installed('datalad','Datalad'):
        install_packages.extend(['datalad-installer','datalad','pyopenssl'])
    
    return install_packages

def install_uv():
    try:
        import uv  # noqa: F401
        return True
    except ImportError:
        try:
            print("Installing 'uv' package into current Python environment...")
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "--upgrade","uv"],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

            print("'uv' installed successfully.")
            
            import uv  # noqa: F401
            return True
        except subprocess.CalledProcessError as e:
            print(f"Failed to install 'uv' via pip: {e}")
            return False

def package_installer(required_libraries: list = None):
    """
    Install missing libraries using uv if available, otherwise fallback to pip.
    Preference order: uv add → uv pip install → pip install
    """

    def safe_uv_add(lib, project_root):
        env = os.environ.copy()
        env["UV_LINK_MODE"] = "copy"

        uv_lock = project_root / "uv.lock"
        if uv_lock.exists():
            try:
                subprocess.run(
                    [sys.executable, "-m", "uv", "add", lib],
                    check=True,
                    env=env,
                    stderr=subprocess.DEVNULL,
                    cwd=project_root
                )
                return True
            except subprocess.CalledProcessError:
                return False
        return False

    def safe_uv_pip_install(lib, project_root):
        env = os.environ.copy()
        env["UV_LINK_MODE"] = "copy"
    
        try:
            subprocess.run(
                [sys.executable, "-m", "uv", "pip", "install", lib],
                check=True,
                env=env,
                stderr=subprocess.DEVNULL,
                cwd=project_root
            )
            return True
        except subprocess.CalledProcessError:
            try:
                subprocess.run(
                    [sys.executable, "-m", "uv", "pip", "install", "--system", lib],
                    check=True,
                    env=env,
                    stderr=subprocess.DEVNULL,
                    cwd=project_root
                )
                return True
            except subprocess.CalledProcessError:
                return False
      

    if not required_libraries:
        return

    try:
        installed_pkgs = {
            name.lower()
            for dist in importlib.metadata.distributions()
            if (name := dist.metadata.get("Name")) is not None
        }
    except Exception as e:
        print(f"⚠️ Error checking installed packages: {e}")
        return

    # Normalize names and find missing ones
    missing_libraries = []
    for lib in required_libraries:
        norm_name = (
            lib.split("==")[0]
               .split(">=")[0]
               .split("<=")[0]
               .split("~=")[0]
               .strip()
               .lower()
        )
        if norm_name not in installed_pkgs:
            if not importlib.util.find_spec(norm_name):
                missing_libraries.append(lib)

    if not missing_libraries:
        return

    #print(f"📦 Installing missing libraries: {missing_libraries}")

    uv_available = install_uv()
    try:
        project_root = PROJECT_ROOT
    except Exception:
        project_root = pathlib.Path.cwd()

    for lib in missing_libraries:
        if uv_available and safe_uv_add(lib, project_root):
            continue

        if uv_available and safe_uv_pip_install(lib, project_root):
            continue

        # Final fallback to pip
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", lib],
                check=True,
                stderr=subprocess.DEVNULL
            )
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install {lib} with pip: {e}")

install_packages = ['python-dotenv']

if sys.version_info < (3, 11):
    install_packages.append('toml')
else:
    install_packages.append('tomli-w')

package_installer(required_libraries = install_packages)

from dotenv import dotenv_values, load_dotenv

if sys.version_info < (3, 11):
    import toml
else:
    import tomllib as toml
    import tomli_w

# ---- Secret manager (optional) ----
try:
    import keyring
    from keyring.errors import KeyringError, NoKeyringError
    _HAS_KEYRING = True
except Exception:
    keyring = None
    KeyringError = NoKeyringError = Exception  # type: ignore
    _HAS_KEYRING = False


def check_path_format(path, project_root=None):
    if not path:
        return path

    if any(sep in path for sep in ["/", "\\", ":"]) and os.path.exists(path):  # ":" for Windows drive letters
        # Set default project root if not provided
        if project_root is None:
            project_root = PROJECT_ROOT

        # Resolve both paths fully
        project_root = pathlib.Path(project_root).resolve()

        # Now adjust slashes depending on platform
        system_name = platform.system()
        if system_name == "Windows":
            path = r"{}".format(path.replace("/", "\\"))
            #path = r"{}".format(path.replace("\\", r"\\"))
        else:  # Linux/macOS
            #path = r"{}".format(path.replace("\\", r"\\"))
            path = r"{}".format(path.replace("\\", "/"))

    return path

# --- Helpers for secret management ---
def _slugify(s: str | None) -> str:
    if not s:
        return "default"
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")

def _project_slug() -> str:
    # 1) explicit override
    s = os.getenv("PROJECT_SLUG") or os.getenv("RT_PROJECT_SLUG")
    if s: return _slugify(s)

    # 2) try git repo name
    try:
        r = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                           capture_output=True, text=True, cwd=str(PROJECT_ROOT))
        if r.returncode == 0:
            return _slugify(pathlib.Path(r.stdout.strip()).name)
    except Exception:
        pass

    # 3) fallback: project folder name
    return _slugify(PROJECT_ROOT.name)

def _secret_service_name() -> str:
    base = os.getenv("SECRET_SERVICE_NAME", "research-template")
    return f"{base}::{_project_slug()}"   # <-- service name is per project

def _keyring_get(name: str) -> str | None:
    """Try project-scoped key first, then global key."""
    if not _HAS_KEYRING:
        return None
    for k in (f"{_project_slug()}:{name}", name):
        try:
            v = keyring.get_password(_secret_service_name(), k)
            if v:
                return v
        except (KeyringError, NoKeyringError):
            return None
    return None

def _keyring_set(name: str, value: str) -> bool:
    """Write project-scoped key. Optionally also write a global alias."""
    if not _HAS_KEYRING:
        return False
    try:
        keyring.set_password(_secret_service_name(), f"{_project_slug()}:{name}", value)
        if os.getenv("SECRET_WRITE_GLOBAL_ALIAS", "").lower() in ("1", "true", "yes"):
            keyring.set_password(_secret_service_name(), name, value)
        return True
    except (KeyringError, NoKeyringError):
        return False

def load_from_env(
    env_name: str,
    env_file: str = ".env",
    toml_file: str = "pyproject.toml",
    use_keyring: bool = True,
) -> str | None:
    """
    Loads a value in this priority order:
      1) keyring / OS secret manager (if enabled and available)
      2) already-set environment variable (os.environ)
      3) .env file (exact path or PROJECT_ROOT/<name>)
      4) [tool.<section>] in TOML fallback (pyproject.toml)
    Returns None if not found.
    """
    if sys.version_info < (3, 11):
        open_mode = ("r", "utf-8")
    else:
        open_mode = ("rb", None)

    name_strip = env_name.strip()
    name_upper = name_strip.upper()

    # 1) Secret manager (keyring)
    if use_keyring:
        val = _keyring_get(name_upper)
        if val:
            return check_path_format(val)

    # 2) Already set in environment
    val = os.getenv(name_upper)
    if val:
        return check_path_format(val)

    # 3) .env path resolve
    env_path = pathlib.Path(env_file)
    if not env_path.is_absolute():
        env_path = PROJECT_ROOT / env_path.name

    if env_path.exists():
        env_values = dotenv_values(env_path)
        if name_upper in env_values and env_values[name_upper]:
            return check_path_format(env_values[name_upper])  # direct read is faster

        # Load into process env and retry
        load_dotenv(env_path, override=True)
        val = os.getenv(name_upper)
        if val:
            return check_path_format(val)

    # If explicitly ".env", DO NOT fallback
    if env_path.name == ".env":
        return None

    # 4) TOML fallback
    toml_section = env_path.stem.lstrip(".")  # e.g. ".cookiecutter" -> "cookiecutter"
    toml_path = pathlib.Path(toml_file)
    if not toml_path.is_absolute():
        toml_path = PROJECT_ROOT / toml_path.name

    if toml_path.exists():
        try:
            with open(toml_path, open_mode[0], encoding=open_mode[1]) as f:
                config = toml.load(f)
            return check_path_format(config.get("tool", {}).get(toml_section, {}).get(name_strip))
        except Exception as e:
            print(f"⚠️ Could not read {toml_path}: {e}")

    return None

def save_to_env(
    env_var: str,
    env_name: str,
    env_file: str = ".env",
    toml_file: str = "pyproject.toml",
    use_keyring: bool = True,
    also_write_file_fallback: bool = True,
) -> None:
    """
    Saves/updates a single secret.
    Default behavior:
      - Try to store in OS secret manager (keyring).
      - If unavailable or disabled, fall back to .env or TOML (original behavior).
    Set also_write_file_fallback=False to avoid file writes when keyring succeeds.
    """

    def sanitize_input(s: str) -> str:
        return s.encode("utf-8", errors="surrogatepass").decode("utf-8", errors="ignore")

    if sys.version_info < (3, 11):
        load_toml = toml.load
        dump_toml = toml.dump
        read_mode = ("r", "utf-8")
        write_mode = ("w", "utf-8")
    else:
        def load_toml(f): return toml.load(f)
        def dump_toml(d, f): f.write(tomli_w.dumps(d))  # type: ignore
        read_mode = ("rb", None)
        write_mode = ("w", "utf-8")

    if env_var is None:
        return

    name_strip = env_name.strip()
    name_upper = name_strip.upper()
    env_var = check_path_format(env_var)
    env_var = sanitize_input(env_var)

    # 1) Try secret manager first
    wrote_keyring = False
    if use_keyring:
        wrote_keyring = _keyring_set(name_upper, env_var)

    # If keyring worked and we don't want file backup, we're done.
    if wrote_keyring and not also_write_file_fallback:
        return

    # 2) File-based fallbacks (your original logic)
    env_path = pathlib.Path(env_file)
    if not env_path.is_absolute():
        env_path = PROJECT_ROOT / env_path.name

    # Always write to .env if explicitly requested or if it already exists
    if env_path.name == ".env" or env_path.exists():
        lines = []
        if env_path.exists():
            with open(env_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

        updated = False
        for i, line in enumerate(lines):
            if "=" in line:
                name, _ = line.split("=", 1)
                if name.strip().upper() == name_upper:
                    lines[i] = f"{name_upper}={env_var}\n"
                    updated = True
                    break
        if not updated:
            lines.append(f"{name_upper}={env_var}\n")

        with open(env_path, "w", encoding="utf-8") as f:
            f.writelines(lines)

        return

    # Fallback: write to [tool.<section>] in TOML
    toml_section = env_path.stem.lstrip(".")
    toml_path = pathlib.Path(toml_file)
    if not toml_path.is_absolute():
        toml_path = PROJECT_ROOT / toml_path.name

    config = {}
    if toml_path.exists():
        try:
            with open(toml_path, read_mode[0], encoding=read_mode[1]) as f:
                config = load_toml(f)
        except Exception as e:
            print(f"⚠️ Could not parse TOML: {e}")
            return

    config.setdefault("tool", {})
    config["tool"].setdefault(toml_section, {})
    config["tool"][toml_section][name_strip] = env_var

    with open(toml_path, write_mode[0], encoding=write_mode[1]) as f:
        dump_toml(config, f)

def exe_to_path(executable: str = None, path: str = None, env_file: str = ".env"):
    """
    Adds the path of an executable binary to the system PATH permanently.
    """

    env_file = pathlib.Path(env_file)
    if not env_file.exists():
        env_file = PROJECT_ROOT / env_file.name

    # Ensure it's an absolute path
    path = os.path.abspath(path)

    os_type = platform.system().lower()
    
    if not executable or not path:
        print("Executable and path must be provided.")
        return False

    if os.path.exists(path):
        # Add to current session PATH
        os.environ["PATH"] += os.pathsep + path

        if os_type == "windows":
            # Use setx to set the environment variable permanently in Windows
            subprocess.run(["setx", "PATH", f"{path};%PATH%"], check=True)
        else:
            # On macOS/Linux, add the path to the shell profile file
            profile_file = os.path.expanduser("~/.bashrc")  # or ~/.zshrc depending on the shell
            with open(profile_file, "a") as file:
                file.write(f'\nexport PATH="{path}:$PATH"')
            # Immediately apply the change for the current script/session (only works if you're in a shell)
            subprocess.run(f'source {profile_file}', shell=True, executable='/bin/bash')
        
        # Check if executable is found in the specified path
        resolved_path = shutil.which(executable)
        
        if resolved_path:
            resolved_path= os.path.abspath(resolved_path)
            resolved_path = os.path.dirname(resolved_path)
            
        if resolved_path == path:
            print(f"{executable} binary is added to PATH and resolved correctly: {path}")
            path = get_relative_path(path)
            save_to_env(path, executable.upper())
            load_dotenv(env_file, override=True)
            return True
        elif resolved_path:
            print(f"{executable} binary available at a wrong path: {resolved_path}")
            print(f"Instead of: {path}")
            resolved_path = get_relative_path(resolved_path)
            save_to_env(resolved_path, executable.upper())
            load_dotenv(env_file, override=True)
            return True
        else:
            print(f"{executable} binary is not found in the specified PATH: {path}")
            return False
    else:
        print(f"{executable}: path does not exist: {path}")
        return False

def remove_from_env(path: str):
    """
    Removes a specific path from the system PATH for the current session and permanently if applicable.
    
    Args:
        path (str): The path to remove from the PATH environment variable.

    Returns:
        bool: True if the path was successfully removed, False otherwise.
    """
    if not path:
        print("No path provided to remove.")
        return False

    # Normalize the path for comparison
    path = os.path.normpath(path)
    
    # Split the current PATH into a list
    current_paths = os.environ["PATH"].split(os.pathsep)
    
    # Remove the specified path
    filtered_paths = [p for p in current_paths if os.path.normpath(p) != path]
    os.environ["PATH"] = os.pathsep.join(filtered_paths)

    # Update PATH permanently
    os_type = platform.system().lower()
    if os_type == "windows":
        # Use setx to update PATH permanently on Windows
        try:
            subprocess.run(["setx", "PATH", os.environ["PATH"]], check=True)
            print(f"Path {path} removed permanently on Windows.")
        except subprocess.CalledProcessError as e:
            print(f"Failed to update PATH permanently on Windows: {e}")
            return False
    else:
        # On macOS/Linux, remove the path from the shell profile file
        profile_file = os.path.expanduser("~/.bashrc")  # or ~/.zshrc depending on the shell
        if os.path.exists(profile_file):
            try:
                with open(profile_file, "r") as file:
                    lines = file.readlines()
                with open(profile_file, "w") as file:
                    for line in lines:
                        if f'export PATH="{path}:$PATH"' not in line.strip():
                            file.write(line)
                print(f"Path {path} removed permanently in {profile_file}.")
            except Exception as e:
                print(f"Failed to update {profile_file}: {e}")
                return False
    return True

def exe_to_env(executable: str = None, path: str = None, env_file: str = ".env"):
    """
    Adds the path of an executable binary to an environment file.
    """

    env_file = pathlib.Path(env_file)
    if not env_file.exists():
        env_file = PROJECT_ROOT / env_file.name

    if not executable:
        print("Executable must be provided.")
        return False

    # Attempt to resolve path if not provided
    if not path or not os.path.exists(path):
        path = os.path.dirname(shutil.which(executable))
    
    if path:
        # Save to environment file
        save_to_env(path, executable.upper())  # Assuming `save_to_env` is defined elsewhere
        load_dotenv(env_file, override=True)

        # Check if executable is found in the specified path
        resolved_path = shutil.which(executable)
        if resolved_path and os.path.dirname(resolved_path) == path:
            print(f"{executable} binary is added to the environment and resolved correctly: {path}")
            save_to_env(path, executable.upper())  # Assuming `save_to_env` is defined elsewhere
            load_dotenv(env_file, override=True)
            return True
        elif resolved_path:
            print(f"{executable} binary available at a wrong path: {resolved_path}")
            save_to_env(os.path.dirname(resolved_path), executable.upper())
            load_dotenv(env_file, override=True) 
            return True
        else:
            print(f"{executable} binary is not found in the specified environment PATH: {path}")
            return False
    else:
        print(f"{executable}:path does not exist: {path}")
        return False

def is_installed(executable: str = None, name: str = None):
    
    if name is None:
        name = executable

    # Check if both executable and name are provided as strings
    if not isinstance(executable, str) or not isinstance(name, str):
        raise ValueError("Both 'executable' and 'name' must be strings.")
    
    path = load_from_env(executable)
    if path:
        path = os.path.abspath(path)

    if path and os.path.exists(path):
        return exe_to_path(executable, path)    
    elif path and not os.path.exists(path):
        remove_from_env(path)

    if shutil.which(executable):
        return exe_to_path(executable, os.path.dirname(shutil.which(executable)))
    else:
        print(f"{name} is not on Path")
        return False

def get_relative_path(target_path):

    if target_path:
        current_dir = os.getcwd()
        absolute_target_path = os.path.abspath(target_path)
        
        # Check if target_path is a subpath of current_dir
        if os.path.commonpath([current_dir, absolute_target_path]) == current_dir:
            # Create a relative path if it is a subpath
            relative_path = os.path.relpath(absolute_target_path, current_dir)

            if relative_path:
                return relative_path
    return target_path

# Setting Options
def git_user_info(version_control):
    if version_control.lower() in ["git", "datalad", "dvc"]:
        # Load defaults


        default_names = split_multi(load_from_env("AUTHORS", ".cookiecutter"))
        default_emails = split_multi(load_from_env("EMAIL", ".cookiecutter"))

        default_name =  default_names[0]
        default_email = default_emails[0]   

        git_name = None
        git_email = None

        while not git_name or not git_email:
            # Prompt with defaults
            name_prompt = f"Enter your Git user name [{default_names[0]}]: "
            email_prompt = f"Enter your Git user email [{default_emails[0]}]: "

            git_name = input(name_prompt).strip() or default_names[0]
            git_email = input(email_prompt).strip() or default_emails[0]

            # Check if inputs are valid
            if not git_name or not git_email:
                print("Both name and email are required.")

        print(f"\nUsing Git user name: {git_name}")
        print(f"Using Git user email: {git_email}\n")

        save_to_env(git_name, 'GIT_USER')
        save_to_env(git_email, 'GIT_EMAIL')
        return git_name, git_email
    else:
        return None, None

def repo_user_info(version_control, repo_name, code_repo):
    valid_repos = ["github", "gitlab", "codeberg"]
    valid_vcs = ["git", "datalad", "dvc"]

    if code_repo.lower() in valid_repos and version_control.lower() in valid_vcs:
        repo_user = None
        privacy_setting = None
        default_setting = "private"
        hostname = None
        default_host = {
            "github": "github.com",
            "gitlab": "gitlab.com",
            "codeberg": "codeberg.org"
        }.get(code_repo.lower())

        while not hostname or not repo_user or not privacy_setting:
            #hostname = input(f"Enter {code_repo} hostname [{default_host}]: ").strip() or default_host
            hostname = default_host
            repo_user = input(f"Enter your {code_repo} username: ").strip()
            privacy_setting = input(f"Select the repository visibility (private/public) [{default_setting}]: ").strip().lower() or default_setting

            if privacy_setting not in ["private", "public"]:
                print("Invalid choice. Defaulting to 'private'.")
                privacy_setting = None

        # Assign keys based on repository
        if code_repo.lower() == "github":
            token_env_key = "GITHUB_TOKEN"
            user_env_key = "GITHUB_USER"
            host_env_key = "GITHUB_HOSTNAME"
            repo_env_key = "GITHUB_REPO"
            privacy_env_key = "GITHUB_PRIVACY"
        elif code_repo.lower() == "gitlab":
            token_env_key = "GITLAB_TOKEN"
            user_env_key = "GITLAB_USER"
            host_env_key = "GITLAB_HOSTNAME"
            repo_env_key = "GITLAB_REPO"
            privacy_env_key = "GITLAB_PRIVACY"
        elif code_repo.lower() == "codeberg":
            token_env_key = "CODEBERG_TOKEN"
            user_env_key = "CODEBERG_USER"
            host_env_key = "CODEBERG_HOSTNAME"
            repo_env_key = "CODEBERG_REPO"
            privacy_env_key = "CODEBERG_PRIVACY"

        # Token retrieval
        token = load_from_env(token_env_key)
        if not token:
            while not token:
                token = getpass.getpass(f"Enter {code_repo} token: ").strip()

        # Save credentials and info
        save_to_env(repo_user, user_env_key)
        save_to_env(privacy_setting, privacy_env_key)
        save_to_env(repo_name, repo_env_key)
        save_to_env(token, token_env_key)
        save_to_env(hostname, host_env_key)

        return repo_user, privacy_setting, token, hostname
    else:
        return None, None, None, None

def remote_user_info(remote_name):
    """Prompt for remote login credentials and base folder path."""

    def ensure_repo_suffix(folder, repo):
        folder = folder.strip().replace("\\", "/").rstrip("/")
        if not folder.endswith(repo):
            return os.path.join(folder, repo).replace("\\", "/")
        return folder

    if remote_name.strip().lower() == "deic storage":
        remote_name = "deic-storage"

    repo_name = load_from_env("REPO_NAME", ".cookiecutter")

    if remote_name.lower() == "deic-storage":

        email = load_from_env("DEIC_EMAIL")
        password = load_from_env("DEIC_PASS")
        base_folder = load_from_env("DEIC_BASE")

        if email and password and base_folder:
            base_folder = ensure_repo_suffix(base_folder, repo_name)
            return email, password, base_folder

        default_email = load_from_env("EMAIL", ".cookiecutter")
        default_base = f'RClone_backup/{repo_name}'
        base_folder = input(f"Enter base folder for {remote_name} [{default_base}]: ").strip() or default_base
        base_folder = ensure_repo_suffix(base_folder, repo_name)

        email = password = None
        while not email or not password:
            email = input(f"Please enter email to Deic-Storage [{default_email}]: ").strip() or default_email
            password = getpass.getpass("Please enter password to Deic-Storage: ").strip()

            if not email or not password:
                print("Both email and password are required.\n")

        print(f"\nUsing email: {email}")
        print(f"Using base folder: {base_folder}\n")

        save_to_env(email, "DEIC_EMAIL")
        save_to_env(password, "DEIC_PASS")
        save_to_env(base_folder, "DEIC_BASE")

        return email, password, base_folder

    elif remote_name.lower() == "local":
        base_folder = input("Please enter the local path for rclone: ").strip().replace("'", "").replace('"', '')
        base_folder = check_path_format(base_folder)
        if not os.path.isdir(base_folder):
            print(f"Error: The specified local path does not exist{base_folder}")
            return None, None, None
        base_folder = ensure_repo_suffix(base_folder, repo_name)
        return None, None, base_folder

    elif remote_name.lower() != "none":
        default_base = f'RClone_backup/{repo_name}'
        base_folder = input(f"Enter base folder for {remote_name} [{default_base}]: ").strip() or default_base
        base_folder = ensure_repo_suffix(base_folder, repo_name)
        return None, None, base_folder

    else:
        return None, None, None

# Setting programming language 

def get_version(programming_language):
    
    if programming_language not in ["python","pip","uv"]:
        exe_path = load_from_env(programming_language)
        exe_path  = check_path_format(exe_path)
        if not exe_path:
            return "Unknown"
    
    if programming_language.lower() == "python":
        version  = f"{subprocess.check_output([sys.executable, '--version']).decode().strip()}"
    elif programming_language.lower() == "r":
        if not exe_path:
            return "R"
        version = subprocess.run([exe_path, '-e', 'cat(paste(R.version$version))'], capture_output=True, text=True)
        version = version.stdout[0:17].strip()
    elif programming_language.lower() == "matlab":
        if not exe_path:
            return "Matlab"
        version = subprocess.run([exe_path, "-batch", "disp(version)"], capture_output=True, text=True)
        version = f"Matlab {version.stdout.strip()}"
    elif programming_language.lower() == "stata":
        if not exe_path:
            return "Stata"
        # Extract edition based on executable name
        edition = "SE" if "SE" in exe_path else ("MP" if "MP" in exe_path else "IC")
        # Extract version from the folder name (e.g., Stata18 -> 18)
        version = os.path.basename(os.path.dirname(exe_path)).replace('Stata', '')
        # Format the output as Stata version and edition
        version = f"Stata {version} {edition}"
    elif programming_language.lower() == "sas": # FIX ME
        if not exe_path:
            return "Sas"
        version = subprocess.run([exe_path, "-version"], capture_output=True, text=True)
        version =version.stdout.strip()  # Returns version info
    elif programming_language.lower() == "pip":
        try:
            version = subprocess.check_output(["pip", "--version"], text=True)
            version = " ".join(version.split()[:2])    
        except subprocess.CalledProcessError as e:
            return "pip"
    elif programming_language.lower() == "uv":
        try:
            version = subprocess.check_output([sys.executable, "-m","uv", "--version"], text=True)
        
            version = version.strip()  # Returns version info       
        except subprocess.CalledProcessError as e:
            return "uv" 
    elif programming_language.lower() == "conda":
        if not exe_path:
            return "conda"   
        version = subprocess.check_output(["conda", "--version"], text=True)
        version = version.strip()  # e.g., "conda 24.3.0"    
    return version

def run_script(programming_language, script_command=None):
    """
    Runs a script or fetches version info for different programming languages.
    
    Args:
        programming_language (str): Programming language name (e.g., 'python', 'r', etc.)
        script_command (str, optional): Script/command to execute. Optional for languages like Stata.
    
    Returns:
        str: Output or version string.
    """
    programming_language = programming_language.lower()

    if programming_language == "python":
        cmd = [sys.executable, "-c", script_command]

    else:
        exe_path = check_path_format(load_from_env(programming_language))
        if not exe_path:
            return "Unknown executable path"

        if programming_language == "r":
            rscript = check_path_format(load_from_env("RSCRIPT"))
            if rscript:
                cmd = [rscript]
                script_command = [script_command[0], script_command[2]]
            else:
                cmd = [exe_path, "--vanilla", "-f"]
            
        elif programming_language == "matlab":
            cmd = [exe_path, "-batch"]

        elif programming_language == "stata":
            cmd = [exe_path, "-b"]

        elif programming_language == "sas":
            cmd = [exe_path, "-SYSIN"]

        else:
            return f"Language {programming_language} not supported."

        cmd.extend(script_command)

    try:
        result = subprocess.run(cmd,capture_output=True, text=True, check=True)
        #result = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return f"Error running script: {e.stderr.strip() if e.stderr else str(e)}"

def make_safe_path(path: str, language: str = "python") -> str:
    """
    Convert a file path to a language-safe format for Python, R, MATLAB, or Stata.
    
    Args:
        path (str): The input file path.
        language (str): One of 'python', 'r', 'matlab', 'stata'.
    
    Returns:
        str: A properly formatted path string.
    """
    language = language.lower()
    path = os.path.abspath(path)

    is_windows = platform.system() == "Windows"

    # Standard form: forward slashes for everything except MATLAB on Windows
    normalized = path.replace("\\", "/") if is_windows else path

    if language == "python":
        return normalized  # Python is tolerant of forward slashes

    elif language == "r":
        return normalized  # R is happy with forward slashes even on Windows

    elif language == "matlab":
        # MATLAB prefers backslashes on Windows, forward slashes on Linux/macOS
        matlab_path = path.replace("/", "\\") if is_windows else path
        return f"'{matlab_path}'"  # Single quotes for MATLAB string

    elif language == "stata":
        return f'"{normalized}"'  # Stata do-files expect double-quoted paths

    else:
        raise ValueError(f"Unsupported language: {language}")

def set_program_path(programming_language):

    if programming_language.lower() not in ["python","none"]:
        exe_path = load_from_env(programming_language.upper())
        
        if not exe_path:
            exe_path = shutil.which(programming_language.lower())
        
        if exe_path:
            save_to_env(check_path_format(exe_path), programming_language.upper())
            save_to_env(get_version(programming_language), f"{programming_language.upper()}_VERSION",".cookiecutter")

    if not load_from_env("PYTHON"):
        save_to_env(sys.executable, "PYTHON")
        save_to_env(get_version("python"), "PYTHON_VERSION",".cookiecutter")

# Maps
ext_map = {
    "r": "R",
    "python": "py",
    "matlab": "m",
    "stata": "do",
    "sas": "sas"
}

language_dirs = {
    "r": "./R",
    "stata": "./stata",
    "python": "./src",
    "matlab": "./src",
    "sas": "./src"
}

#Check software
def ensure_correct_kernel(func):
    """Decorator to ensure the function runs with the correct Python kernel."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        python_kernel = load_from_env("PYTHON")  # Load the desired kernel path from the environment
        
        # If no specific kernel is set, just run the function normally
        if not python_kernel:
            return func(*args, **kwargs)
        
        os_type = platform.system().lower()
        if os_type == "windows":
            py_exe = "python.exe"
        elif os_type == "darwin" or os_type == "linux":
            py_exe = "python"

        # If the kernel path doesn't contain "python.exe", append it
        if not python_kernel.endswith(py_exe):
            python_kernel = os.path.join(python_kernel, py_exe)

        # Get the current executable and its base folder
        current_executable = sys.executable
        current_base = os.path.dirname(current_executable)
        kernel_base = os.path.dirname(python_kernel)

        # If the current Python executable does not match the required kernel, restart
        if current_executable != python_kernel and current_base != kernel_base:
            print(f"Restarting with the correct Python kernel: {python_kernel}")

            # Re-run the script with the correct Python interpreter
            script_path = os.path.abspath(__file__)
            subprocess.run([python_kernel, script_path] + sys.argv[1:], check=True)
            sys.exit()  # Terminate the current process after restarting

        # If the kernel is correct, execute the function normally
        return func(*args, **kwargs)

    return wrapper

def write_uv_requires(toml_file: str = "pyproject.toml"):
    """Writes 'project.requires-python = >=<version>' to the given pyproject.toml."""
    version_str = subprocess.check_output([sys.executable, "--version"]).decode().strip().split()[1]
    requires = f">= {version_str}"

    # TOML loading/dumping
    if sys.version_info < (3, 11):
        load_toml = toml.load
        dump_toml = toml.dump
        read_mode = ("r", "utf-8")
        write_mode = ("w", "utf-8")
    else:
        def load_toml(f): return toml.load(f)
        def dump_toml(d, f): f.write(tomli_w.dumps(d))
        read_mode = ("rb", None)
        write_mode = ("w", "utf-8")

    path = pathlib.Path(toml_file)
    if not path.is_absolute():
        path = PROJECT_ROOT / path.name

    config = {}
    if path.exists():
        with open(path, read_mode[0], encoding=read_mode[1]) as f:
            config = load_toml(f)

    config.setdefault("project", {})
    config["project"]["requires-python"] = requires
    #config["tool"]["uv"]["python"] = version_str

    with open(path, write_mode[0], encoding=write_mode[1]) as f:
            dump_toml(config, f)

@contextmanager
def change_dir(destination):
    cur_dir = os.getcwd()
    destination = str(PROJECT_ROOT / pathlib.Path(destination))
    try:
        os.chdir(destination)
        yield
    finally:
        os.chdir(cur_dir)

if load_from_env("VENV_ENV_PATH") or load_from_env("CONDA_ENV_PATH"):
    package_installer(required_libraries = set_packages(load_from_env("VERSION_CONTROL",".cookiecutter"),load_from_env("PROGRAMMING_LANGUAGE",".cookiecutter")))

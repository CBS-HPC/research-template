import os
import subprocess
from subprocess import DEVNULL
import sys
import platform
import shutil
from functools import wraps
import pathlib
import importlib.metadata
import importlib.util
from dotenv import load_dotenv

if sys.version_info < (3, 11):
    import toml
    tomli_w = None
else:
    import tomllib as toml
    import tomli_w

from .base import install_uv, PROJECT_ROOT
from .paths import check_path_format, get_relative_path  
from .secretstore import load_from_env, save_to_env

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

def set_packages(version_control,programming_language):

    if not programming_language or not version_control:
        return []

    install_packages = ['python-dotenv','pyyaml','requests','beautifulsoup4','nbformat','setuptools','pathspec','psutil','py-cpuinfo','jinja2','streamlit','jsonschema','dirhash']

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
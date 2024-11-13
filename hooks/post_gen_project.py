import os
import subprocess
import sys
import platform
import urllib.request
import os

def get_hardware_info():
    """
    Extract hardware information and save it to a file.
    Works on Windows, Linux, and macOS.
    """
    system = platform.system()
    command = ""

    if system == "Windows":
        command = "systeminfo"
    elif system == "Linux":
        command = "lshw -short"  # Alternative: "dmidecode"
    elif system == "Darwin":  # macOS
        command = "system_profiler SPHardwareDataType"
    else:
        print("Unsupported operating system.")
        return

    try:
        # Execute the command and capture the output
        hardware_info = subprocess.check_output(command, shell=True, text=True)

        # Save the hardware information to a file
        with open("hardware_information.txt", "w") as file:
            file.write(hardware_info)

        print("Hardware information saved to hardware_information.txt")

    except subprocess.CalledProcessError as e:
        print(f"Error retrieving hardware information: {e}")

def setup_virtual_environment(version_control,virtual_environment,repo_platform,repo_name,install_path = "bin/miniconda"):
    """
    Create a virtual environment for Python or R based on the specified programming language.
    
    Parameters:
    - repo_name: str, name of the virtual environment.
    - programming_language: str, 'python' or 'R' to specify the language for the environment.
    """

    def get_file_path():
        """
        Prompt the user to provide the path to a .yml or .txt file and check if the file exists and is the correct format.
        
        Returns:
        - str: Validated file path if the file exists and has the correct extension.
        """

        # Prompt the user for the file path
        file_path = input("Please enter the path to a .yml or .txt file: ").strip()
            
        # Check if the file exists
        if not os.path.isfile(file_path):
            print("The file does not exist. Please try again.")
            return None
            
        # Check the file extension
        _, file_extension = os.path.splitext(file_path)
        if file_extension.lower() not in {'.yml', '.txt'}:
            print("Invalid file format. The file must be a .yml or .txt file.")
            return None
        
        # If both checks pass, return the valid file path
        return file_path
   
    def create_venv_env(env_name):
        """Create a Python virtual environment using venv."""
        subprocess.run([sys.executable, '-m', 'venv', env_name], check=True)
        print(f'Venv environment "{repo_name}" for Python created successfully.')

    def create_virtualenv_env(env_name):
        """Create a Python virtual environment using virtualenv."""
        subprocess.run(['virtualenv', env_name], check=True)
        print(f'Virtualenv environment "{repo_name}" for Python created successfully.')
        

    install_packages = ['python']
    #install_packages = ['-c conda-forge','python']
    env_file  = None

    if virtual_environment not in ['Python','R','environment.yaml','requirements.txt']:
        return
    
    # Ask for user confirmation
    confirm = input(f"Do you want to create a virtual environment named '{repo_name}' for/from {virtual_environment}? (yes/no): ").strip().lower()
    
    if confirm != 'yes':
        print("Virtual environment creation canceled.")
        return
    
    if virtual_environment in ['environment.yaml','requirements.txt']:
        env_file = get_file_path()
        if env_file is None:
            return None

    if virtual_environment in ['Python','R','environment.yaml','requirements.txt']:

        if virtual_environment == 'R':
             install_packages.extend(['r-base'])  
        if version_control == 'Git':
             install_packages.extend(['git'])   
        if version_control == 'DVC':
             install_packages.extend(['git','dvc, dvc-ssh'])    
        elif version_control == 'Datalad':
             install_packages.extend(['git','rclone'])
        if repo_platform == 'GitHub':
             install_packages.extend(['gh'])     
            
        check = setup_conda(install_path,virtual_environment,repo_name, install_packages,env_file)

        if check is False and virtual_environment == 'Python':
            if subprocess.call(['which', 'virtualenv']) == 0:
                create_virtualenv_env(repo_name)
            else:
                create_venv_env(repo_name)
        elif virtual_environment == 'R': 
            print('Conda is not installed. Please install it to create an {programming_language}  environment.')

        return repo_name

def setup_conda(install_path,virtual_environment,repo_name, install_packages = [], env_file = None):
            
    def is_conda_installed(check = True):
        """Check if conda is installed."""
        
        if check is False:
            return check
        try:
            subprocess.run(['conda', '--version'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def install_miniconda(check,install_path):
        """
        Downloads and installs Miniconda to a specified location based on the operating system.
        
        Parameters:
        - install_path (str): The absolute path where Miniconda should be installed.

        Returns:
        - bool: True if installation is successful, False otherwise.
        """
        if check:
            return check
        
        system = platform.system().lower()
        installer_name = None
        download_dir = os.path.dirname(install_path)  # One level up from the install_path
        installer_path = None
        
        if system == "windows":
            installer_name = "Miniconda3-latest-Windows-x86_64.exe"
            url = f"https://repo.anaconda.com/miniconda/{installer_name}"
            installer_path = os.path.join(download_dir, installer_name)
            install_command = [installer_path, "/InstallationType=JustMe", f"/AddToPath=0", f"/RegisterPython=0", f"/S", f"/D={install_path}"]
            
        elif system == "darwin":  # macOS
            installer_name = "Miniconda3-latest-MacOSX-arm64.sh" if platform.machine() == "arm64" else "Miniconda3-latest-MacOSX-x86_64.sh"
            url = f"https://repo.anaconda.com/miniconda/{installer_name}"
            installer_path = os.path.join(download_dir, installer_name)
            install_command = ["bash", installer_path, "-b", "-p", install_path]
            
        elif system == "linux":
            installer_name = "Miniconda3-latest-Linux-x86_64.sh"
            url = f"https://repo.anaconda.com/miniconda/{installer_name}"
            installer_path = os.path.join(download_dir, installer_name)
            install_command = ["bash", installer_path, "-b", "-p", install_path]
            
        else:
            print("Unsupported operating system.")
            return False
        
        try:
            print(f"Downloading {installer_name} from {url} to {download_dir}...")
            urllib.request.urlretrieve(url, installer_path)
            print("Download complete.")
            
            print("Installing Miniconda...")
            subprocess.run(install_command, check=True)
            if installer_path and os.path.exists(installer_path):
                os.remove(installer_path)
            print("Miniconda installation complete.")
            return True
            
        except Exception as e:
            if installer_path and os.path.exists(installer_path):
                os.remove(installer_path)
            print(f"Failed to install Miniconda: {e}")
            return False

    def add_miniconda_to_path(check,install_path):
        """
        Adds Miniconda's bin (Linux/Mac) or Scripts (Windows) directory to the system PATH.

        Parameters:
        - install_path (str): The absolute path where Miniconda is installed.

        Returns:
        - bool: True if addition to PATH is successful, False otherwise.
        """
        if check is False:
            return check
    
        system = platform.system().lower()
        conda_bin_path = os.path.join(install_path, 'Scripts' if system == 'windows' else 'bin')
        
        try:
            if system == 'windows':
                subprocess.run(f'setx PATH "%PATH%;{conda_bin_path}"', shell=True, check=True)
                print("Miniconda path added to system PATH (permanent for Windows).")
            else:
                shell_profile = os.path.expanduser("~/.bashrc" if system == "linux" else "~/.zshrc")
                with open(shell_profile, "a") as file:
                    file.write(f'\n# Miniconda path\nexport PATH="{conda_bin_path}:$PATH"\n')
                os.environ["PATH"] = f"{conda_bin_path}:{os.environ['PATH']}"
                print(f"Miniconda path added to PATH. Please restart your terminal or source your {shell_profile} to apply.")
            return True
            
        except Exception as e:
            print(f"Failed to add Miniconda to PATH: {e}")
            return False

    def initialize_conda_shell(check):
        """
        Initializes Conda for the user's shell by running `conda init` and starting a new interactive shell session.

        Returns:
        - bool: True if Conda shell initialization is successful, False otherwise.
        """
        if check is False:
            return check
        system = platform.system().lower()

        try:
            subprocess.run(["conda", "init"], check=True)
            print("Conda shell initialization complete.")
            
            #if system == "windows":
            #    print("Please restart your terminal to apply the changes.")
            #elif system == "linux" or system == "darwin":
            #    print("Starting a new shell session to apply Conda setup...")
            #    subprocess.run(["bash", "-i"])
            return True

        except Exception as e:
            print(f"Failed to initialize Conda shell: {e}")
            return False

    def create_conda_env(command,msg):
        """
        Create a conda environment from an environment.yml file with a specified name.
        
        Parameters:
        - env_file: str, path to the environment YAML file. Defaults to 'environment.yml'.
        - env_name: str, optional name for the new environment. If provided, overrides the name in the YAML file.
        """
        try:
  
            # Run the command
            subprocess.run(command, check=True)
            print(msg)
            
        except subprocess.CalledProcessError as e:
            print(f"Failed to create conda environment: {e}")
        except FileNotFoundError:
            print("Conda is not installed or not found in the system path.")
        except Exception as e:
            print(f"An error occurred: {e}")

    def generate_yml(env_name,requirements_path):
        """Generate an environment.yml file using a requirements.txt file."""
        yml_content = f"""
            name: {env_name}
            channels:
            - conda-forge
            dependencies:
            - python>=3.5
            - anaconda
            - pip
            - pip:
                - -r file:{requirements_path}
            """
        with open('environment.yml', 'w') as yml_file:
            yml_file.write(yml_content)
        print(f"Generated environment.yml file using {requirements_path}.")

    def export_conda_env(env_name, output_file='environment.yml'):
        """
        Export the details of a conda environment to a YAML file.
        
        Parameters:
        - env_name: str, name of the conda environment to export.
        - output_file: str, name of the output YAML file. Defaults to 'environment.yml'.
        """
        try:
            # Use subprocess to run the conda export command
            with open(output_file, 'w') as f:
                subprocess.run(['conda', 'env', 'export', '-n', env_name], stdout=f, check=True)
            
            print(f"Conda environment '{env_name}' exported to {output_file}.")

        except subprocess.CalledProcessError as e:
            print(f"Failed to export conda environment: {e}")
        except FileNotFoundError:
            print("Conda is not installed or not found in the system path.")
        except Exception as e:
            print(f"An error occurred: {e}")
               
    check = is_conda_installed()
    if check is False:
        check = install_miniconda(check,install_path)
        check = add_miniconda_to_path(check,install_path)
        check = initialize_conda_shell(check)

    if check:
        if virtual_environment in ['Python','R']:
            command = ['conda', 'create','--yes', '--name', repo_name]
            if install_packages:
                command.extend(install_packages)
            #command.extend(['--yes'])
            msg = f'Conda environment "{repo_name}" for {virtual_environment} created successfully. The following packages were installed: {install_packages}'
        elif virtual_environment in ['environment.yaml','requirements.txt']:
            if virtual_environment == 'requirements.txt':
                generate_yml(repo_name,env_file)
            command = ['conda', 'env', 'create', '-f', env_file, '--name', repo_name]
            msg = f'Conda environment "{repo_name}" created successfully from {virtual_environment}.'
        
        create_conda_env(command,msg)
        export_conda_env(repo_name)
    
    return check

def run_python_script(script_path, env_name=None, conda_path=None):
    """
    Runs a Python script in a specified Conda environment. If no environment is specified,
    the base Python environment is used.

    Parameters:
    - script_path (str): Path to the Python script to execute.
    - env_name (str or None): Name of the Conda environment to activate. If None, uses the base Python environment.
    - conda_path (str or None): Path to the Conda installation. Defaults to CONDA_PREFIX or Conda base if None.
    """
    # Determine the OS-specific shell
    shell = '/bin/bash' if os.name != 'nt' else 'cmd.exe'

    def set_conda(env_name, conda_path):
        """
        Determines the path to the Conda activate script and constructs the activation command.
        
        Parameters:
        - env_name (str): Name of the Conda environment to activate.
        - conda_path (str or None): Path to the Conda installation. If None, uses the base or CONDA_PREFIX.

        Returns:
        - str: The command to activate the Conda environment.
        """
        # Locate the Conda activate script
        if conda_path:
            conda_activate = os.path.join(conda_path, "bin", "activate")
        else:
            conda_prefix = os.environ.get("CONDA_PREFIX")
            if conda_prefix:
                conda_activate = os.path.join(conda_prefix, "bin", "activate")
            else:
                # Fallback: Use 'conda info --base' to locate Conda's base environment
                try:
                    conda_info = subprocess.run(
                        ["conda", "info", "--base"], capture_output=True, text=True, check=True
                    )
                    conda_base = conda_info.stdout.strip()
                    conda_activate = os.path.join(conda_base, "bin", "activate")
                except subprocess.CalledProcessError:
                    raise EnvironmentError("Could not locate Conda base environment. Ensure Conda is installed.")
        
        # Construct the activation command
        if shell == '/bin/bash':
            return f"source {conda_activate} && conda activate {env_name}"
        else:
            return f"{conda_activate} {env_name} &&"

    # Construct the full command based on the environment setting
    if env_name:
        activate_cmd = set_conda(env_name, conda_path)
        full_command = f"{activate_cmd} && python {script_path}"
    else:
        # No env_name provided, use the base Python environment
        full_command = f"python {script_path}"

    # Run the command
    try:
        result = subprocess.run(full_command, shell=True, executable=shell, check=True)
        print("Script executed successfully.")
        return result
    except subprocess.CalledProcessError as e:
        print(f"An error occurred: {e}")
        sys.exit(e.returncode)

def run_bash_script(script_path, repo_name=None, setup_version_control_path=None, setup_remote_repository_path=None):
    try:
        # Make sure the script is executable
        os.chmod(script_path, 0o755)

        # Run the script with the additional paths as arguments
        subprocess.check_call(['bash', '-i', script_path, repo_name, setup_version_control_path, setup_remote_repository_path])  # Pass repo_name and paths to the script
        print(f"Script {script_path} executed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while executing the script: {e}")

setup_version_control = "setup/version_control.py"
setup_remote_repository = "setup/remote_repository.py"
setup_bash_script = "setup/create.sh"
miniconda_path =  "bin/miniconda"

virtual_environment = "{{ cookiecutter.virtual_environment}}"
repo_name = "{{ cookiecutter.repo_name }}"
repo_platform = "{{ cookiecutter.repository_platform}}"
version_control = "{{cookiecutter.version_control}}"
remote_storage = "{{cookiecutter.remote_storage}}"

# Create Virtual Environment
repo_name = setup_virtual_environment(version_control,virtual_environment,repo_platform,repo_name,miniconda_path)

run_bash_script(setup_bash_script, repo_name, setup_version_control, setup_remote_repository)



import os
import subprocess
import sys
import shutil
import platform

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

def create_virtual_environment():
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
        
    def check_conda():
        """Check if conda is installed."""
        try:
            subprocess.run(['conda', '--version'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def create_conda_env(env_name, programming_language):
        """Create a conda environment."""
        subprocess.run(['conda', 'create', '--name', env_name, programming_language, '--yes'], check=True)
        print(f'Conda environment "{env_name}" for {programming_language} created successfully.')

    def create_from_yml(env_name=None,yml_file='environment.yml'):
        """
        Create a conda environment from an environment.yml file with a specified name.
        
        Parameters:
        - env_file: str, path to the environment YAML file. Defaults to 'environment.yml'.
        - env_name: str, optional name for the new environment. If provided, overrides the name in the YAML file.
        """
        try:
            # Construct the command
            command = ['conda', 'env', 'create', '-f', yml_file]
            if env_name:
                command.extend(['--name', env_name])  # Add the specified name

            # Run the command
            subprocess.run(command, check=True)
            print(f"Conda environment '{env_name or 'default name in YAML'}' created successfully from {yml_file}.")

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

    def create_venv_env(env_name):
        """Create a Python virtual environment using venv."""
        subprocess.run([sys.executable, '-m', 'venv', env_name], check=True)
        print(f'Venv environment "{repo_name}" for Python created successfully.')

    def create_virtualenv_env(env_name):
        """Create a Python virtual environment using virtualenv."""
        subprocess.run(['virtualenv', env_name], check=True)
        print(f'Virtualenv environment "{repo_name}" for Python created successfully.')

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
                

    repo_name = "{{ cookiecutter.repo_name }}"
    virtual_environment = "{{ cookiecutter.virtual_environment}}"

    if virtual_environment.lower() not in ['python','r','environment.yaml','requirements.txt']:
        return
    
    # Ask for user confirmation
    confirm = input(f"Do you want to create a virtual environment named '{repo_name}' for/from {virtual_environment}? (yes/no): ").strip().lower()
    
    if confirm != 'yes':
        print("Virtual environment creation canceled.")
        return
    
    if virtual_environment.lower() in ['environment.yaml','requirements.txt']:
        env_file = get_file_path()
        if env_file is None:
            return

    if virtual_environment.lower() in ['python','r','environment.yaml','requirements.txt']:
        if check_conda():
            if virtual_environment.lower() in ['python','r']:
                create_conda_env(repo_name,virtual_environment)
            elif virtual_environment.lower() in ['environment.yaml']:
                create_from_yml(repo_name,env_file)
            elif virtual_environment.lower() in ['requirements.txt']:
                generate_yml(repo_name,env_file)
                create_from_yml(repo_name,env_file)
            export_conda_env(repo_name)
        elif virtual_environment.lower() == 'python':
            if subprocess.call(['which', 'virtualenv']) == 0:
                create_virtualenv_env(repo_name)
            else:
                create_venv_env(repo_name)
        elif virtual_environment.lower() == 'r': 
            print('Conda is not installed. Please install it to create an {programming_language}  environment.')

def is_git_installed():
    try:
        # Run 'git --version' and capture the output
        output = subprocess.check_output(['git', '--version'], stderr=subprocess.STDOUT)
        # Decode the output from bytes to string and check if it contains 'git version'
        if 'git version' in output.decode('utf-8'):
            return True
    except FileNotFoundError:
        print("Git is not installed or not in the system PATH.")
    except subprocess.CalledProcessError:
        print("An error occurred while checking Git version.")
    return False

def git_init(platform):
    # Initialize a Git repository if one does not already exist
    if not os.path.isdir(".git"):
        subprocess.run(["git", "init"], check=True)
        print("Initialized a new Git repository.")

    if platform == "GitHub":
        # Rename branch to 'main' if it was initialized as 'master'
        subprocess.run(["git", "branch", "-m", "master", "main"], check=True)

    subprocess.run(["git", "add", "."], check=True)    
    subprocess.run(["git", "commit", "-m", "Initial commit"], check=True)
    print("Created an initial commit.")

def is_datalad_installed():
    try:
        # Run 'datalad --version' and capture the output
        output = subprocess.check_output(['datalad', '--version'], stderr=subprocess.STDOUT)
        # Decode the output from bytes to string and check if it contains 'datalad'
        if 'datalad' in output.decode('utf-8'):
            print("DataLad is installed.")
            return True
    except FileNotFoundError:
        print("DataLad is not installed or not in the system PATH.")
    except subprocess.CalledProcessError:
        print("An error occurred while checking DataLad version.")
    return False

def install_datalad():
    try:
        # Step 1: Install datalad-installer via pip
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'datalad-installer'])

        # Step 2: Install git-annex using datalad-installer
        subprocess.check_call(['datalad-installer', 'git-annex', '-m', 'datalad/git-annex:release'])

        # Step 3: Set recommended git-annex configuration for performance improvement
        subprocess.check_call(['git', 'config', '--global', 'filter.annex.process', 'git-annex filter-process'])

        # Step 4: Install DataLad with pip
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'datalad'])

    except subprocess.CalledProcessError as e:
        print(f"An error occurred: {e}")
    except FileNotFoundError:
        print("One of the required commands was not found. Please ensure Python, pip, and Git are installed and in your PATH.")

def datalad_create():

    def create_backup(files_to_backup,backup_dir):

        # Check if backup directory exists, create it if not
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)

         # Backup the specified files
        for file in files_to_backup:
            if os.path.exists(file):
                shutil.copy(file, os.path.join(backup_dir, file))
                #print(f"Backed up {file}.")

    def remove_backup(files_to_backup,backup_dir):
        
        # Prevent git-annex from handling specific files
        for file in files_to_backup:
            if os.path.exists(file):
                # Use git annex add with --skip option to ignore these files
                subprocess.run(["git", "annex", "add", "--skip", file], check=True)
                print(f"Prevented {file} from being managed by git-annex.")

        # Restore the backed-up files
        for file in files_to_backup:
            backup_file_path = os.path.join(backup_dir, file)
            if os.path.exists(backup_file_path):
                shutil.copy(backup_file_path, file)

        # Remove the backup files
        shutil.rmtree(backup_dir)
   
    def unlock_files(filenames):
        """
        Unlock multiple files using git annex.

        Parameters:
        filenames (list): A list of filenames to unlock.
        """
        for filename in filenames:
            try:
                # Run the git annex unlock command for each file
                subprocess.run(["git", "annex", "unlock", filename], check=True)
            except subprocess.CalledProcessError as e:
                print(f"Error unlocking {filename}: {e}")
            except FileNotFoundError:
                print("git annex is not found. Please ensure it is installed and available in PATH.")

    # Initialize a Git repository if one does not already exist
    if not os.path.isdir(".datalad"):
        files_to_unlock = ["README.md", "LICENSE", "hardware_information.txt"]
        #backup_dir = "backup_files"
        #create_backup(files_to_backup,backup_dir)
        subprocess.run(["datalad", "create","--force"], check=True)
        unlock_files(files_to_unlock )
        subprocess.run(["datalad", "save", "-m", "Initial commit"], check=True)
        print("Created an initial commit.")
        #remove_backup(files_to_backup,backup_dir)

def github_login(username,privacy_setting):
    
    repo_name = "{{ cookiecutter.repo_name }}"
    description = "{{ cookiecutter.description }}"

    # Login if necessary
    login_status = subprocess.run(["gh", "auth", "status"], capture_output=True, text=True)
    if "You are not logged into any GitHub hosts" in login_status.stderr:
        print("Not logged into GitHub. Attempting login...")
        subprocess.run(["gh", "auth", "login"], check=True)

    # Create the GitHub repository
    subprocess.run([
        "gh", "repo", "create", f"{username}/{repo_name}",
        f"--{privacy_setting}", "--description", description, "--source", ".", "--push"
    ])

def gitlab_login(username,privacy_setting):  # FIX ME !! Not working
    repo_name = "{{ cookiecutter.repo_name }}"
    description = "{{ cookiecutter.description }}"


    # Login if necessary
    login_status = subprocess.run(["glab", "auth", "status"], capture_output=True, text=True)
    if "Not logged in" in login_status.stderr:
        print("Not logged into GitLab. Attempting login...")
        subprocess.run(["glab", "auth", "login"], check=True)

    # Create the GitLab repository
    subprocess.run([
        "glab", "repo", "create", f"{username}/{repo_name}",
        f"--{privacy_setting}", "--description", description, "--source", ".", "--push"
    ])

def install_requirements():
    """Install the required packages from requirements.txt."""
    # Get the directory of the current script (which is in hooks)
    hook_dir = os.path.dirname(os.path.abspath(__file__))
    requirements_path = os.path.join(hook_dir, '..', 'requirements.txt')

    try:
        subprocess.run(["pip", "install", "-r", requirements_path], check=True)
    except FileNotFoundError:
        print("requirements.txt not found. Please ensure it is located in the project root directory.")
        exit(1)
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while trying to install requirements: {e}")
        exit(1)

def handle_repo_creation():
    """Handle repository creation and log-in based on selected platform."""
    platform = "{{ cookiecutter.repository_platform }}"
    version_control = "{{cookiecutter.version_control}}"
    git_check = is_git_installed()
    
    if version_control == None or git_check is False:
        return
    
    elif version_control == "Git":
        git_init(platform)
    elif version_control == "Datalad":
        datalad_check = is_datalad_installed()
        if datalad_check is False:
            install_datalad()
        datalad_create()


    if platform in ["GitHub", "GitLab"]:

        username = input(f"Enter your {platform} username: ").strip()

        privacy_setting = input("Select the repository visibility (private/public): ").strip().lower()
        
        if privacy_setting not in ["private", "public"]:
            print("Invalid choice. Defaulting to 'private'.")
            privacy_setting = "private"

        if platform == "GitHub":
            github_login(username,privacy_setting)
        elif platform == "GitLab":
            gitlab_login(username,privacy_setting)
    else:
        print("No repository platform selected; skipping repository creation.")

# Install requirements
#nstall_requirements()

# Create Virtual Environment
create_virtual_environment()

# Get Hardware information
get_hardware_info()

# Handle repository creation
handle_repo_creation()

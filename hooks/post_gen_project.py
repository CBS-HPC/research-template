import os
import subprocess
import sys
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
    programming_language = "{{ cookiecutter.virtual_environment}}"

    if programming_language.lower() not in ['python','r']:
        return
    
    # Ask for user confirmation
    confirm = input(f"Do you want to create a virtual environment named '{repo_name}' for {programming_language}? (yes/no): ").strip().lower()
    
    if confirm != 'yes':
        print("Virtual environment creation canceled.")
        return
    
    if programming_language.lower() not in ['python','r']:
        if check_conda():
            create_conda_env(repo_name,programming_language)
            export_conda_env(repo_name)
        elif programming_language.lower() == 'python':
            if subprocess.call(['which', 'virtualenv']) == 0:
                create_virtualenv_env(repo_name)
            else:
                create_venv_env(repo_name)
        elif programming_language.lower() == 'r': 
            print('Conda is not installed. Please install it to create an {programming_language}  environment.')


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

def gitlab_login(username,privacy_setting):
    repo_name = "{{ cookiecutter.repo_name }}"
    description = "{{ cookiecutter.description }}"


    # Login if necessary
    login_status = subprocess.run(["glab", "auth", "status"], capture_output=True, text=True)
    if "Not logged in" in login_status.stderr:
        print("Not logged into GitLab. Attempting login...")
        subprocess.run(["glab", "auth", "login"], check=True)


    # Create the GitHub repository
   # subprocess.run(["gh", "repo", "create", repo_name, "--private"], check=True)
    #print(f"GitHub repository '{repo_name}' created successfully and linked to local repo.")
        
    # Link and push to the GitHub repository
    #subprocess.run(["git", "remote", "add", "origin", f"https://github.com/{username}/{repo_name}.git"], check=True)
    #subprocess.run(["git", "push", "-u", "origin", "main"], check=True)
    #print("Pushed initial commit to GitHub on main branch.")


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
    if platform in ["GitHub", "GitLab"]:

        git_init(platform)

        username = input(f"Enter your {platform} username: ").strip()

        privacy_setting = input("Select the repository visibility(private/public): ").strip().lower()
        
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

# Get Hardware information
get_hardware_info()

# Create Virtual Environment
create_virtual_environment()

# Handle repository creation
handle_repo_creation()

import os
import subprocess

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

def save_env_file(platform, username):
    with open(".env", "w") as f:
        f.write(f"REPOSITORY_PLATFORM={platform}\n")
        f.write(f"GIT_USERNAME={username}\n")

def handle_repo_creation():
    platform = "{{ cookiecutter.repository_platform }}"
    if platform in ["GitHub", "GitLab"]:
        username = input(f"Enter your {platform} username: ").strip()
        save_env_file(platform, username)
    else:
        print("No repository platform selected; skipping repository creation.")

# Install requirements
#nstall_requirements()

# Handle repository creation
handle_repo_creation()

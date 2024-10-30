import os
import subprocess

def install_requirements():
    """Install the required packages from requirements.txt."""
    subprocess.run(["pip", "install", "-r", "requirements.txt"], check=True)

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
install_requirements()

# Handle repository creation
handle_repo_creation()

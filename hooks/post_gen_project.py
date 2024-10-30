import os
import subprocess

def github_login(username):
    
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
        "--private", "--description", description, "--source", ".", "--push"
    ])

def git_init():
    # Initialize a Git repository if one does not already exist
    if not os.path.isdir(".git"):
        subprocess.run(["git", "init"], check=True)
        print("Initialized a new Git repository.")


    # Create an initial commit to ensure there’s content to push
    with open(".gitkeep", "w") as f:
        f.write("")  # Add an empty file as a placeholder

    subprocess.run(["git", "add", "."], check=True)    
    subprocess.run(["git", "commit", "-m", "Initial commit"], check=True)
    print("Created an initial commit.")



def gitlab_login(username):
    repo_name = "{{ cookiecutter.repo_name }}"
    description = "{{ cookiecutter.description }}"

    # Rename branch to 'main' if it was initialized as 'master'
    subprocess.run(["git", "branch", "-m", "master", "main"], check=True)

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
        "--private", "--description", description, "--source", ".", "--push"
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
        
        git_init()


        username = input(f"Enter your {platform} username: ").strip()
        if platform == "GitHub":
            github_login(username)
        elif platform == "GitLab":
            gitlab_login(username)
    else:
        print("No repository platform selected; skipping repository creation.")

# Install requirements
#nstall_requirements()

# Handle repository creation
handle_repo_creation()

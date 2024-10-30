import subprocess

# Replace these with actual values from cookiecutter.json
repo_name = "{{ cookiecutter.repo_name }}"
gitlab_username = "{{ cookiecutter.gitlab_username }}"
description = "{{ cookiecutter.description }}"

if not gitlab_username:
    print("GitLab username is not provided. Skipping GitLab login and repository creation.")
    exit(0)

def check_glab_auth():
    """Checks if the user is authenticated with GitLab CLI."""
    try:
        # Check if the user is logged in with `glab auth status`
        result = subprocess.run(["glab", "auth", "status"], capture_output=True, text=True)
        
        if "not authenticated" in result.stdout.lower():
            print("GitLab CLI not authenticated. Attempting to log in...")
            subprocess.run(["glab", "auth", "login"], check=True)
            print("GitLab CLI login successful.")
        else:
            print("GitLab CLI authentication confirmed.")
    
    except subprocess.CalledProcessError:
        print("Error during GitLab CLI login process. Please try manually with 'glab auth login'.")
        exit(1)  # Exit if authentication fails

def create_gitlab_repo():
    """Creates a new private GitLab repository."""
    try:
        subprocess.run([
            "glab", "repo", "create", f"{gitlab_username}/{repo_name}",
            "--private", "--description", description
        ], check=True)
        print(f"Private GitLab repository '{repo_name}' created successfully under {gitlab_username}.")

        # Add the remote origin to the local git repository
        subprocess.run(["git", "remote", "add", "origin", f"https://gitlab.com/{gitlab_username}/{repo_name}.git"], check=True)
        print("Remote 'origin' added to the local repository.")

    except subprocess.CalledProcessError as e:
        print("Error occurred during GitLab repository creation:", e)
    except FileNotFoundError:
        print("GitLab CLI (glab) is not installed. Please install it from https://github.com/profclems/glab")

# Step 1: Check authentication status and log in if necessary
check_glab_auth()

# Step 2: Create the GitLab repository
create_gitlab_repo()

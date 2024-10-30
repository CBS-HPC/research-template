import subprocess

# Replace these with actual values from cookiecutter.json
repo_name = "{{ cookiecutter.repo_name }}"
github_username = "{{ cookiecutter.github_username }}"
description = "{{ cookiecutter.description }}"

if not github_username:
    print("GitHub username is not provided. Skipping GitHub login and repository creation.")
    exit(0)

def check_gh_auth():
    """Checks if the user is authenticated with GitHub CLI."""
    try:
        # Capture the output of `gh auth status`
        result = subprocess.run(["gh", "auth", "status"], capture_output=True, text=True)
        
        # Check if the output indicates the user is not logged in
        if "You are not logged into any GitHub hosts" in result.stdout:
            print("GitHub CLI not authenticated. Attempting to log in...")
            subprocess.run(["gh", "auth", "login"], check=True)
            print("GitHub CLI login successful.")
        else:
            print("GitHub CLI authentication confirmed.")

    except subprocess.CalledProcessError as e:
        print("Error during GitHub CLI login process. Please try manually with 'gh auth login'.")
        exit(1)  # Exit if authentication fails

def create_github_repo():
    """Creates a new private GitHub repository."""
    try:
        subprocess.run([
            "gh", "repo", "create", f"{github_username}/{repo_name}",
            "--private", "--description", description, "--confirm"
        ], check=True)
        print(f"Private GitHub repository '{repo_name}' created successfully under {github_username}.")

        # Add the remote origin to the local git repository
        subprocess.run(["git", "remote", "add", "origin", f"https://github.com/{github_username}/{repo_name}.git"], check=True)
        print("Remote 'origin' added to the local repository.")

    except subprocess.CalledProcessError as e:
        print("Error occurred during GitHub repository creation:", e)
    except FileNotFoundError:
        print("GitHub CLI (gh) is not installed. Please install it from https://cli.github.com/")

# Step 1: Check authentication status and log in if necessary
check_gh_auth()

# Step 2: Create the GitHub repository
create_github_repo()

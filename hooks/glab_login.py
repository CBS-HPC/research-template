import os
import subprocess

def gitlab_login(username):
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
        "--private", "--description", description, "--source", ".", "--push"
    ])

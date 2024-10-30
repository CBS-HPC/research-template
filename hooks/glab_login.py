import os
from dotenv import load_dotenv
import subprocess

load_dotenv()

platform = os.getenv("REPOSITORY_PLATFORM")
username = os.getenv("GIT_USERNAME")
repo_name = "{{ cookiecutter.repo_name }}"
description = "{{ cookiecutter.description }}"

if platform == "GitLab" and username:
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

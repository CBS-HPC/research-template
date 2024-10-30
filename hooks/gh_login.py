import os
from dotenv import load_dotenv
import subprocess

load_dotenv()

platform = os.getenv("REPOSITORY_PLATFORM")
username = os.getenv("GIT_USERNAME")
repo_name = "{{ cookiecutter.repo_name }}"
description = "{{ cookiecutter.description }}"

if platform == "GitHub" and username:
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
import subprocess

def handle_repo_creation():
    platform = "{{ cookiecutter.repository_platform }}"    
    if platform == "GitHub":
        github_username = "{{ cookiecutter.github_username }}"
        if github_username:
            # Run the GitHub login and repository creation script
            subprocess.run(["python", "gh_login.py"], check=True)
    
    elif platform == "GitLab":
        gitlab_username = "{{ cookiecutter.gitlab_username }}"
        if gitlab_username:
            # Run the GitLab login and repository creation script
            subprocess.run(["python", "glab_login.py"], check=True)

handle_repo_creation()
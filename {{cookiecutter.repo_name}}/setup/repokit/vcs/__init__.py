# utils/__init__.py
import os
import pathlib

from ..backup import install_rclone
from ..common import (
    PROJECT_ROOT,
    change_dir,
    save_to_env,
)
from .git_w import (
    install_git,
    git_init,
    git_log_to_file,
    check_git_config,
    setup_git_config,
    git_commit,
    git_push
)
from .datalad_w import (
    install_git_annex,
    install_datalad,
    datalad_create,
    datalad_local_storage,
    datalad_deic_storage,
    install_git_annex_remote_rclone,
    set_datalad,
    datalad_cleaning,
)
from .dvc_w import (
    install_dvc,
    dvc_init,
    dvc_deic_storage,
    dvc_local_storage,
    set_dvc,
    dvc_cleaning
)


# Setup functions
def setup_version_control(version_control, remote_storage, code_repo, repo_name):
    """Handle repository creation and log-in based on selected platform."""
    if version_control.lower() == "git":
        setup_git(version_control, code_repo)
    if version_control.lower() == "datalad":
        setup_datalad(version_control, remote_storage, code_repo, repo_name)
    elif version_control.lower() == "dvc":
        setup_dvc(version_control, remote_storage, code_repo, repo_name)


def setup_git(version_control, code_repo):
    if install_git("./bin/git"):
        # Ensure that chdir is at project folder
        os.chdir(PROJECT_ROOT)

        flag, git_name, git_email = check_git_config()

        if not flag:
            flag, git_name, git_email = setup_git_config(version_control, git_name, git_email)

        if flag and version_control.lower() in ["git","datalad","dvc"]: 
            
            default_branch = "main" if code_repo.lower() in ["github", "codeberg"] else "master"
            
            flag = git_init(msg="Initial commit", branch_name=default_branch)
            # Creating its own git repo for "data"
            if version_control.lower() == "git" and flag:
                with change_dir("./data"):
                    flag = git_init(msg="Initial commit - /data git repo", branch_name="data", path=os.getcwd())
                    git_log_to_file(os.path.join(".gitlog"))
        if flag:
            save_to_env(git_name, "GIT_USER")
            save_to_env(git_email, "GIT_EMAIL")

        return flag
    else:
        return False


def setup_dvc(version_control, remote_storage, code_repo, repo_name):
    # Install Git
    if not setup_git(version_control, code_repo):
        return

    # Install datalad
    if not install_dvc():
        return
    
 
    # deactivate data/ in .gitignore
    gitignore = pathlib.Path(PROJECT_ROOT / ".gitignore")
    if gitignore.exists():
        lines = gitignore.read_text().splitlines()
        new_lines = [line.replace("data/", "#data/") if line.startswith("data/") else line for line in lines]
        gitignore.write_text("\n".join(new_lines) + "\n")
    
    dvc_init(remote_storage, code_repo, repo_name)


def setup_datalad(version_control, remote_storage, code_repo, repo_name):
    # Install Git
    if not setup_git(version_control, code_repo):
        return
    # Install git-annex
    if not install_git_annex():
        return
    # Install datalad
    if not install_datalad():
        return

    # Install rclone git-annex-remote-rclone
    install_rclone("./bin")
    install_git_annex_remote_rclone("./bin")

    # deactivate data/ in .gitignore
    gitignore = pathlib.Path(PROJECT_ROOT / ".gitignore")
    if gitignore.exists():
        lines = gitignore.read_text().splitlines()
        new_lines = [line.replace("data/", "#data/") if line.startswith("data/") else line for line in lines]
        gitignore.write_text("\n".join(new_lines) + "\n")

    # Create datalad dataset
    datalad_create()

    if remote_storage == "Local Path":
        datalad_local_storage(repo_name, remote_storage)
    elif remote_storage in ["Dropbox", "Deic-Storage"]:
        datalad_deic_storage(repo_name)


# Public API
__all__ = [
    # High-level setup functions
    "setup_version_control",
    "setup_git",
    "setup_dvc",
    "setup_datalad",

    
    # Git functions
    "install_git",
    "git_init",
    "git_log_to_file",
    "check_git_config",
    "setup_git_config",
    "git_commit",
    "git_push",
    
    # DataLad functions
    "install_git_annex",
    "install_datalad",
    "datalad_create",
    "datalad_local_storage",
    "datalad_deic_storage",
    "install_git_annex_remote_rclone",
    "set_datalad",
    "datalad_cleaning",

    
    # DVC functions
    "install_dvc",
    "dvc_init",
    "dvc_deic_storage",
    "dvc_local_storage",
    "set_dvc",
    "dvc_cleaning",
]

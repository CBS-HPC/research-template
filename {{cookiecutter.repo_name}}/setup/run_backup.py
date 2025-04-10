import os
import pathlib
import argparse

from utils import *

@ensure_correct_kernel
def run_backup(remote_backups,repo_name):
    
    if remote_backups.lower() != "none": 
        if install_rclone("./bin"):
            remote_backups= [item.strip() for item in remote_backups.split(",")]
            for remote_backup in remote_backups:
                if check_rclone_remote(remote_backup.lower()):
                    rclone_repo = load_from_env("RCLODE_REPO")
                else:
                    email, password = remote_user_info(remote_backup.lower())
                    rclone_remote(remote_backup.lower(),email, password)
                    rclone_repo = rclone_folder(remote_backup.lower(), 'RClone_backup/' + repo_name)
            
                if rclone_repo:
                    rclone_sync(rclone_repo, folder_to_backup=None)

def main():
    # Change to project root directory
    project_root = pathlib.Path(__file__).resolve().parent.parent
    os.chdir(project_root)

    # Add command-line argument parsing
    parser = argparse.ArgumentParser(description="Run backup process")
    parser.add_argument('--repo_name', type=str, default=None, help="Repository name")
    parser.add_argument('--remote_backup', type=str, default=None, help="Comma separated remote backups")
    args = parser.parse_args()

    repo_name = args.repo_name or load_from_env("REPO_NAME", ".cookiecutter")
    remote_backup = args.remote_backup or load_from_env("REMOTE_BACKUP", ".cookiecutter")
    run_backup(remote_backup, repo_name)

if __name__ == "__main__":
    main()
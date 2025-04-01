import sys

sys.path.append('setup')
from utils import *


def run_backup(remote_backup,repo_name):
    if remote_backup.lower() == "deic storage":
        install_rclone("bin")

        if check_rclone_remote("deic-storage"):
            rclone_repo = load_from_env("RCLODE_REPO")
        else:
            rclone_remote("deic-storage")
            rclone_repo= rclone_folder("deic-storage", 'RClone_backup/' + repo_name)
       
        if rclone_repo:
           rclone_copy(rclone_repo, folder_to_backup=None)
       
if __name__ == "__main__":
    repo_name = load_from_env("REPO_NAME",".cookiecutter")
    remote_backup = load_from_env("REMOTE_BACKUP",".cookiecutter")

    # Setup Remote Backup
    run_backup(remote_backup,repo_name)
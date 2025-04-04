
from utils import *

@ensure_correct_kernel
def run_backup(remote_backups,repo_name):
    
    if remote_backup.lower() != "none": 
        if install_rclone("bin"):
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
       
if __name__ == "__main__":

    repo_name = load_from_env("REPO_NAME",".cookiecutter")
    remote_backup = load_from_env("REMOTE_BACKUP",".cookiecutter")
    run_backup(remote_backup,repo_name)
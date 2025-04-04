
from utils import *

@ensure_correct_kernel
def run_backup(remote_backup,repo_name):
    if remote_backup.lower() in ["deic storage","dropbox","onedrive"]:
        if install_rclone("bin"):

            if check_rclone_remote(remote_backup.lower()):
                rclone_repo = load_from_env("RCLODE_REPO")
            else:
                rclone_remote(remote_backup.lower())
                rclone_repo = rclone_folder(remote_backup.lower(), 'RClone_backup/' + repo_name)
        
            if rclone_repo:
                rclone_sync(rclone_repo, folder_to_backup=None)
       
if __name__ == "__main__":

    repo_name = load_from_env("REPO_NAME",".cookiecutter")
    remote_backup = load_from_env("REMOTE_BACKUP",".cookiecutter")
    
    run_backup(remote_backup,repo_name)

    #if not check_python_kernel():
    #    python_kernel = load_from_env("PYTHON")  # Load the desired kernel path from environment
    #    # If the python_kernel path doesn't already contain "python.exe", append it
    #    if "python.exe" not in python_kernel:
    #        python_kernel = os.path.join(python_kernel, "python.exe")     
    #    script_path = os.path.abspath(__file__)  # Get the current script path
    #    change_python_kernel(python_kernel, script_path)  # Restart the script with the new kernel
    #else:
    #    repo_name = load_from_env("REPO_NAME",".cookiecutter")
    #    remote_backup = load_from_env("REMOTE_BACKUP",".cookiecutter")

        # Setup Remote Backup
    #    run_backup(remote_backup,repo_name)
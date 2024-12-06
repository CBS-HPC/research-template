
import sys


# Add the directory to sys.path
script_dir = "setup"
if script_dir not in sys.path:
    sys.path.append(script_dir)

from utils import update_file_descriptions,create_tree

setup_version_control = "setup/version_control.py"
setup_remote_repository = "setup/remote_repository.py"
setup_bash_script = "setup/create.sh"
setup_powershell_script = "setup/create.ps1"

miniconda_path =  "bin/miniconda"

virtual_environment = "Python"
repo_name = "ghe_"
code_repo = "GitHub"
version_control = "Git"
remote_storage = "None"
project_name = "ghe_"
project_description = "hello"

# Create and update README and Project Tree:
update_file_descriptions("README.md", json_file="setup/file_descriptions.json")
create_tree("README.md", ['.git','.datalad','.gitkeep','.env','__pycache__'] ,"setup/file_descriptions.json")
import os
import subprocess
import sys
import os

# Add the directory to sys.path
script_dir = "setup"
if script_dir not in sys.path:
    sys.path.append(script_dir)

#virtual_environment = "{{ cookiecutter.virtual_environment}}"
# Creates default scripts:
#create_scripts(virtual_environment, "src")


# Run the script
subprocess.run(["python", "setup/create.py"])

import os
import subprocess
import sys
import platform
import urllib.request
import os
import shutil

# Add the directory to sys.path
script_dir = "setup"
if script_dir not in sys.path:
    sys.path.append(script_dir)


# main_script.py
import subprocess


# Run the script
subprocess.run(["python", "setup/create.py"])



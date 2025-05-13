import subprocess
#import sys
import pathlib
import os

# Add the directory to sys.path
#script_dir = "setup"
#if script_dir not in sys.path:
#    sys.path.append(script_dir)


PROJECT_DIR = pathlib(os.path.realpath(os.curdir))

folders = [
    PROJECT_DIR/"data" / "00_raw",
    PROJECT_DIR/"data" / "01_interim",
    PROJECT_DIR/"data" / "02_processed",
    PROJECT_DIR/"data" / "03_external",
]

for folder in folders:
    folder.mkdir(parents=True, exist_ok=True)
    (folder / ".gitkeep").touch(exist_ok=True)


# Run the script
subprocess.run(["python", "setup/project_setup.py"])



import os
import sys
import json
import argparse
import subprocess
from datetime import datetime
import pathlib

# Ensure the project root is in sys.path
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

# Ensure the working directory is the project root
project_root = pathlib.Path(__file__).resolve().parent.parent
os.chdir(project_root)

from utils import *

def get_file_info(file_paths):
    """
    Takes a list of full file paths and returns:
    - number of files
    - total size in MB
    - set of unique file formats (extensions)
    - list of individual file sizes
    """
    number_of_files = 0
    total_size = 0
    file_formats = set()
    individual_sizes = []

    print(file_paths)
    for path in file_paths:
        print(path)
        # If it's a file
        number_of_files += 1
        file_size = os.path.getsize(path) / (1024 * 1024)
        total_size += file_size
        individual_sizes.append(int(file_size))
        file_formats.add(os.path.splitext(path)[1].lower())

    #total_size /= 1024 * 1024  # Convert total size to MB
    return number_of_files, total_size, file_formats, individual_sizes

def get_file_info_old(path):
    if os.path.isfile(path):
        # If it's a single file
        number_of_files = 1
        total_size = os.path.getsize(path) / (1024 * 1024)  # in MB
        file_formats = {os.path.splitext(path)[1].lower()}
    elif os.path.isdir(path):
        # Recursively walk through all subfolders and files
        number_of_files = 0
        total_size = 0
        file_formats = set()
        
        for root, _, files in os.walk(path):
            for f in files:
                full_path = os.path.join(root, f)
                if os.path.isfile(full_path):
                    number_of_files += 1
                    total_size += os.path.getsize(full_path)
                    file_formats.add(os.path.splitext(f)[1].lower())
        
        total_size /= 1024 * 1024  # Convert to MB
    else:
        raise ValueError(f"Path does not exist or is not a file/folder: {path}")
    
    return number_of_files, total_size, file_formats

def get_all_files(destination):
    """
    Returns a set of all file paths within the given directory,
    including files in all subdirectories.
    """
    all_files = set()
    for root, dirs, files in os.walk(destination):
        for file in files:
            full_path = os.path.join(root, file)
            all_files.add(full_path)
    return all_files

def add_to_json(json_file_path, entry):
    """
    Adds or updates an entry in the JSON file.

    Parameters:
        json_file_path (str): Path to the JSON file.
        entry (dict): The dataset metadata to add or update.
    """
  
    json_file_path = str(pathlib.Path(__file__).resolve().parent.parent.parent /  pathlib.Path(json_file_path))
    
    if os.path.exists(json_file_path):
        with open(json_file_path, "r") as json_file:
            datasets = json.load(json_file)
    else:
        datasets = []

    # Check if the dataset already exists
    if entry["hash"]:
        existing_entry = next((item for item in datasets if item["data_name"] == entry["data_name"] and item["destination"] == entry["destination"] and item["hash"] == entry["hash"]),None)
    else:
        existing_entry = next((item for item in datasets if item["data_name"] == entry["data_name"] and item["destination"] == entry["destination"]), None)
    
    if existing_entry:
        # Update the existing entry
        datasets[datasets.index(existing_entry)] = entry
        print(f"Updated existing dataset entry for {entry['data_name']}.")

    elif not existing_entry :
        # Add a new entry
        datasets.append(entry)
        print(f"Added new dataset entry for {entry['data_name']}.")

    # Write updated datasets to the JSON file
    with open(json_file_path, "w") as json_file:
        json.dump(datasets, json_file, indent=4)
    print(f"Metadata saved to {json_file_path}")

    return json_file_path

def set_dataset(data_name, destination, source:str = None, run_command:str = None,json_file_path:str = "./datasets.json" , doi:str = None,citation:str = None,license:str=None):
    """
    Executes a data download process and tracks created files in the specified path.

    Parameters:
        data_name (str): Name of the dataset.
        source (str): The remote URL or path to the dataset.
        run_command (str): A command for executing the download function/script.
                           The script will ensure {source} and {destination} are appended.
        destination (str): The path where the data will be stored. Defaults to './data/raw/data_name' if None.
    """
    destination = check_path_format(destination)

    if os.path.isfile(destination):
        data_files = [destination]
    else:
        os.makedirs(destination, exist_ok=True)
        initial_files = get_all_files(destination)

        if run_command:
            command_parts = run_command.split()
            command_list = command_parts + [source, destination]

            if is_installed(command_parts[0]):
                try:
                    result = subprocess.run(command_list, check=True, text=True, capture_output=True)
                    print(f"Command output:\n{result.stdout}")
                except subprocess.CalledProcessError as e:
                    print(f"Error executing command: {e}")
                    print(f"Command output:\n{e.output}")
                    return
            else:
                raise FileNotFoundError(f"The executable '{command_parts[0]}' was not found in the PATH.")
            
            updated_files = get_all_files(destination)
            data_files = list(updated_files - initial_files)
        else:
            data_files = list(initial_files)
        data_files = sorted(data_files)

    number_of_files, total_size, file_formats, individual_sizes = get_file_info(data_files)

    if number_of_files > 1000: # FIX ME !!
        print("It is recommended to zip datasets with >1000 files when creating a replication package: https://aeadataeditor.github.io/aea-de-guidance/preparing-for-data-deposit.html#data-structure-of-a-replication-package")


    hash= get_git_hash(destination)

    new_entry = {
        "data_name": data_name,
        "destination": destination,
        "hash":None,
        "number_of_files": number_of_files,
        "total_size_mb": int(total_size),
        "file_formats": list(file_formats),
        "timestamp": datetime.now().isoformat(),
        "data_files": data_files,
        "data_size": individual_sizes,
    }

    if hash:
        new_entry["hash"] = hash

    if source:
        new_entry["source"] = source

    if run_command:
        new_entry["run_command"] = " ".join(command_list)

    if doi:
        new_entry["DOI"] = doi

    if citation:
        new_entry["citation"] = citation
    
    if license:
        new_entry["license"] = license

    # Add or update the JSON metadata
    json_file_path = add_to_json(json_file_path, new_entry)

    return json_file_path

@ensure_correct_kernel
def set_datasets(data_name:str= None, source:str=None, run_command:str=None, destination:str=None, doi:str = None,citation:str = None,license:str=None):
    
    def sanitize_folder_name(name):
        return name.replace(" ", "_").replace("/", "_").replace("\\", "_").replace(":", "_")
    
    def get_data_files():
        # Subdirectories to look into
        subdirs = ['raw', 'interim', 'processed', 'external']
        base_dir = './data'

        # Gather all files and folders with full paths, excluding Git-related files
        all_files = []
        for subdir in subdirs:
            dir_path = os.path.join(base_dir, subdir)
            if not os.path.exists(dir_path):
                continue  # Skip if the directory doesn't exist
            for item in os.listdir(dir_path):
                full_path = os.path.join(dir_path, item)
                if (
                    os.path.isdir(full_path) or
                    (os.path.isfile(full_path) and not item.startswith(".git") and item not in [".gitignore", ".gitkeep"])
                ):
                    all_files.append(full_path)

        return all_files

    # If all input parameters are None, gather all files and folders from './data/raw/'
    if all(param is None for param in [data_name, source, run_command, destination, doi, citation, license]):
        data_files = get_data_files()
        for file in data_files:
            json_file_path = set_dataset(data_name=os.path.basename(file), destination=file, source=None, run_command=None, json_file_path="./data/datasets.json", doi=None, citation=None, license=None) 
    else:
        if destination is None:
            destination = f"./data/raw/{sanitize_folder_name(data_name)}"
        json_file_path = set_dataset(data_name = data_name, destination = destination, source=source, run_command=run_command, json_file_path="./data/datasets.json", doi=doi, citation=citation, license=license)

    try:
        markdown_table, full_table = generate_dataset_table(json_file_path)
        dataset_to_readme(markdown_table)

        with open("DCAS template/dataset_list.md", 'w') as markdown_file:
            markdown_file.write(full_table)
    except Exception as e:
        print(e)


def main():
    parser = argparse.ArgumentParser(description="Set data source and monitor file creation.")
    parser.add_argument("--name", default=None, help="Name of the dataset.")
    parser.add_argument("--source", default=None, help="Remote URL or path to the dataset.")
    parser.add_argument("--command", default=None, help="Command for executing the download function/script.")
    parser.add_argument("--destination", default=None, help="Path where data will be stored (optional).")
    parser.add_argument("--doi", default=None, help="DOI of the dataset (optional).")
    parser.add_argument("--citation", default=None, help="Citation of the dataset (optional).")
    parser.add_argument("--license", default=None, help="License of the dataset (optional).")
    
    args = parser.parse_args()

    # Call the function to handle the dataset setup
    set_datasets(args.name, args.source, args.command, args.destination, args.doi, args.citation, args.license)


if __name__ == "__main__":
    
    # Change to project root directory
    project_root = pathlib.Path(__file__).resolve().parent.parent.parent
    os.chdir(project_root)
    
    main()


#python setup/set_raw_data.py deic_dataset1 "https://sid.storage.deic.dk/cgi-sid/ls.py?share_id=CyOR8W3h2f" "./setup/deic_storage_download.py"
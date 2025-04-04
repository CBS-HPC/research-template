import os
import json
import argparse
import subprocess
from datetime import datetime
import pathlib

from utils import *
from readme_templates import *

# Change to project root directory
project_root = pathlib.Path(__file__).resolve().parent.parent
os.chdir(project_root)

def set_data(data_name, source, run_command, destination:str=None, doi:str = None,citation:str = None,license:str=None):
    """
    Executes a data download process and tracks created files in the specified path.

    Parameters:
        data_name (str): Name of the dataset.
        source (str): The remote URL or path to the dataset.
        run_command (str): A command for executing the download function/script.
                           The script will ensure {source} and {destination} are appended.
        destination (str): The path where the data will be stored. Defaults to './data/raw/data_name' if None.
    """

    def sanitize_folder_name(name):
        return name.replace(" ", "_").replace("/", "_").replace("\\", "_").replace(":", "_")
    
    def get_file_info(destination):
        files = [f for f in os.listdir(destination) if os.path.isfile(os.path.join(destination, f))]
        number_of_files = len(files)
        total_size = sum(os.path.getsize(os.path.join(destination, f)) for f in files) / (1024 * 1024)
        file_formats = set(os.path.splitext(f)[1].lower() for f in files)
        return number_of_files, total_size, file_formats

    def add_to_json(json_file_path, entry):
        """
        Adds or updates an entry in the JSON file.

        Parameters:
            json_file_path (str): Path to the JSON file.
            entry (dict): The dataset metadata to add or update.
        """
        if os.path.exists(json_file_path):
            with open(json_file_path, "r") as json_file:
                datasets = json.load(json_file)
        else:
            datasets = []

        # Check if the dataset already exists
        existing_entry = next((item for item in datasets if item["data_name"] == entry["data_name"] and item["destination"] == entry["destination"]), None)
        if existing_entry:
            # Update the existing entry
            datasets[datasets.index(existing_entry)] = entry
            print(f"Updated existing dataset entry for {entry['data_name']}.")
        else:
            # Add a new entry
            datasets.append(entry)
            print(f"Added new dataset entry for {entry['data_name']}.")

        # Write updated datasets to the JSON file
        with open(json_file_path, "w") as json_file:
            json.dump(datasets, json_file, indent=4)
        print(f"Metadata saved to {json_file_path}")

    if destination is None:
        destination = f"./data/raw/{sanitize_folder_name(data_name)}"
    json_file_path = "./datasets.json"

    os.makedirs(destination, exist_ok=True)

    initial_files = set(os.listdir(destination))
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

    updated_files = set(os.listdir(destination))
    data_files = list(updated_files - initial_files)
    number_of_files, total_size, file_formats = get_file_info(destination)

    if number_of_files > 1000: # FIX ME !!
        print("It is recommended to zip datasets with >1000 files when creating a replication package: https://aeadataeditor.github.io/aea-de-guidance/preparing-for-data-deposit.html#data-structure-of-a-replication-package")

    new_entry = {
        "data_name": data_name,
        "source": source,
        "destination": destination,
        "run_command": " ".join(command_list),
        "number_of_files": number_of_files,
        "total_size_mb": total_size,
        "file_formats": list(file_formats),
        "data_files": data_files,
        "timestamp": datetime.now().isoformat(),
    }

    if doi:
        new_entry["DOI"] = doi

    if citation:
        new_entry["citation"] = citation
    
    if license:
        new_entry["license"] = license

    # Add or update the JSON metadata
    add_to_json(json_file_path, new_entry)

    try:
        markdown_table, full_table = generate_dataset_table(json_file_path)
        append_dataset_to_readme(markdown_table)

        with open("dataset_list.md", 'w') as markdown_file:
            markdown_file.write(full_table)
    except Exception as e:
        print(e)

@ensure_correct_kernel
def set_raw_data(data_name, source, run_command, destination:str=None, doi:str = None,citation:str = None,license:str=None):
    
    if destination is None:
        destination = f"./data/raw/{sanitize_folder_name(data_name)}"
    
    set_data(data_name, source, run_command, destination, doi,citation,license)

def save_datalist(full_table ,markdown_file_path="dataset_list.md"):

    # Save the markdown table to a file
    with open(markdown_file_path, 'w') as markdown_file:
            markdown_file.write(full_table)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Set data source and monitor file creation.")
    parser.add_argument("--name", required=True, help="Name of the dataset.")
    parser.add_argument("--source", required=True, help="Remote URL or path to the dataset.")
    parser.add_argument("--command", required=True, help="Command for executing the download function/script.")
    parser.add_argument("--destination", default=None, help="Path where data will be stored (optional).")
    parser.add_argument("--doi", default=None, help="DOI of the dataset (optional).")
    parser.add_argument("--citation", default=None, help="Citation of the dataset (optional).")
    parser.add_argument("--license", default=None, help="License of the dataset (optional).")
    args = parser.parse_args()

    set_raw_data(args.data_name, args.source, args.command, args.destination, args.doi, args.citation,args.license)


#python set_raw_data.py deic_dataset1 "https://sid.storage.deic.dk/cgi-sid/ls.py?share_id=CyOR8W3h2f" "./src/deic_storage_download.py"
import os
import json
import argparse
import subprocess
from datetime import datetime
import sys
import pathlib


# Change to project root directory
project_root = pathlib.Path(__file__).resolve().parent.parent
os.chdir(project_root)

# Add the directory to sys.path
script_dir = "setup"
if script_dir not in sys.path:
    sys.path.append(script_dir)

from utils import *


def set_raw_data(data_name, source, run_command, destination=None, doi=None):
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

    # Add or update the JSON metadata
    add_to_json(json_file_path, new_entry)

    try:
        markdown_table, full_table = generate_markdown_table(json_file_path)
        append_to_readme(markdown_table)

        with open("dataset_list.md", 'w') as markdown_file:
            markdown_file.write(full_table)
    except Exception as e:
        print(e)

def generate_markdown_table(json_file_path):
    """
    Generates a markdown table based on the data in a JSON file.

    Parameters:
        json_file_path (str): Path to the JSON file containing dataset metadata.

    Returns:
        str: A markdown formatted table as a string.
    """
    
    # Check if the JSON file exists
    if not os.path.exists(json_file_path):
        raise FileNotFoundError(f"The file {json_file_path} does not exist.")
    
    # Read the JSON file
    with open(json_file_path, 'r') as json_file:
        data = json.load(json_file)

    # If the data is a list, loop through each dataset entry
    if isinstance(data, list):
        markdown_table = (
            f"| Name             | Location        | Provided        | Run Command               | Number of Files | Total Size (MB) | File Formats         | Source          | DOI                | Notes                  |\n"
            f"|------------------|-----------------|-----------------|---------------------------|-----------------|-----------------|----------------------|-----------------|--------------------|------------------------|\n"
        )

        full_table = (
            f"| Name                  | Files                             | Location        | Provided        | Run Command               | Source           | DOI             | Notes                |\n"
            f"|-----------------------|-----------------------------------|-----------------|-----------------|---------------------------|------------------|-----------------|----------------------|\n"
        )

        for entry in data:
            if isinstance(entry, dict):  # Only process dictionary entries
                # Extract required information from the JSON data
                data_name = entry.get("data_name", "N/A")
                data_files = " ; ".join(entry.get("data_files", ["Not available"]))  # Newline separated
                location = entry.get("destination", "N/A")
                provided = "Provided" if entry.get("data_files") else "Can be re-created"
                run_command = entry.get("run_command", "N/A")
                number_of_files = entry.get("number_of_files", 0)
                total_size_mb = entry.get("total_size_mb", 0)
                file_formats = "; ".join(entry.get("file_formats", ["Not available"]))
                source = entry.get("source", "N/A")
                doi = entry.get("DOI", "Not provided")
                notes = entry.get("notes", "No additional notes")


                 # Format pdf table
                data_files = entry.get("data_files", ["Not available"])
                for file in data_files:
                    full_table += (f"|{data_name}| {file}|{location}|{provided}|{run_command}|{source}|{doi}| {notes}|\n")

                # Format the markdown table for this entry
                markdown_table += (f"|{data_name}| {location}| {provided}|{run_command}|{number_of_files}|{total_size_mb}|{file_formats}|{source}|{doi}|{notes}|\n")
       

        
        return markdown_table,full_table


    else:
        # If the data is not a list, raise an error
        raise TypeError(f"Expected a list of datasets but got {type(data)}.")

def append_to_readme(markdown_table, readme_path:str= 'README.md'):
    """
    Appends the generated markdown table to the README file under the 
    'Dataset List' heading.

    Parameters:
        markdown_table (str): The markdown table to be appended.
        readme_path (str): The path to the README file.
    """
    # Read the current content of the README file
    with open(readme_path, 'r') as readme_file:
        content = readme_file.readlines()

    # Check if the 'Data Availability and Provenance Statements' section exists
    heading_found = False
    for i, line in enumerate(content):
        if "Dataset List" in line:
            heading_found = True
            # Insert the markdown table below the heading
            content.insert(i + 1, markdown_table + "\n")
            break
    
    # If the heading is not found, add it at the end
    if not heading_found:
        content.append("\n# Dataset List\n")
        content.append(markdown_table + "\n")

    # Write the updated content back to the README
    with open(readme_path, 'w') as readme_file:
        readme_file.writelines(content)
    print(f"Appended data to {readme_path}")

def save_datalist(full_table ,markdown_file_path="dataset_list.md"):

    # Save the markdown table to a file
    with open(markdown_file_path, 'w') as markdown_file:
            markdown_file.write(full_table)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Set data source and monitor file creation.")
    parser.add_argument("--data_name", required=True, help="Name of the dataset.")
    parser.add_argument("--source", required=True, help="Remote URL or path to the dataset.")
    parser.add_argument("--run_command", required=True, help="Command for executing the download function/script.")
    parser.add_argument("--destination", default=None, help="Path where data will be stored (optional).")
    parser.add_argument("--doi", default=None, help="DOI of the dataset (optional).")
    args = parser.parse_args()

    # Execute the function with command-line arguments
    set_raw_data(args.data_name, args.source, args.run_command, args.destination, args.doi)


#python set_raw_data.py deic_dataset1 "https://sid.storage.deic.dk/cgi-sid/ls.py?share_id=CyOR8W3h2f" "./src/deic_storage_download.py"
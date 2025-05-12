import os
import json
import argparse
import subprocess
from datetime import datetime
import pathlib
from collections import defaultdict

from .readme_templates import *
from .versioning_tools import *

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

def add_to_json(json_file_path:str = "./datasets.json", entry=None):
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

    # Find existing by destination
    existing_index = next(
        (i for i, d in enumerate(datasets) if d.get("destination") == entry.get("destination")),
        None
    )

    if existing_index is not None:
        existing_entry = datasets[existing_index]

    existing_entry = next(
            (item for item in datasets
            if item["destination"] == entry["destination"]),
            None
        )

    if existing_entry:
        flag = False
        if entry.get("hash") and existing_entry["hash"] != entry["hash"]:   
            flag = True
        elif not all(existing_entry.get(key) == val for key, val in entry.items()if val is not None and key not in ("created")):
            flag = True
        if flag:
            existing_entry['lastest_change'] = entry['created']  
            # Update only the fields in existing_entry that are not None in entry
            for key, value in entry.items():
                if value is not None:
                    existing_entry[key] = value
            
            # **Re-assign into the list** so we don't accidentally drop changes
            datasets[existing_index] = existing_entry

            print(f"Updated existing dataset entry for {entry['data_name']}.")

    elif not existing_entry :        
        if not entry["data_name"]:
            entry["data_name"] = os.path.basename(entry["destination"])
        # Add a new entry
        datasets.append(entry)
        print(f"Added new dataset entry for {entry['data_name']}.")


    # Define a key function that copes with missing or None values
    def sort_key(entry: dict) -> str:
        value = entry.get("data_type", "")
        return value

    # Sort in-place, or use `sorted(datasets, key=sort_key)` to return a new list
    datasets.sort(key=sort_key)

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
        destination (str): The path where the data will be stored. Defaults to './data/00_raw/data_name' if None.
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
        "data_type":  os.path.basename(os.path.dirname(destination)),
        "destination": destination,
        "hash":None,
        "number_of_files": number_of_files,
        "total_size_mb": int(total_size),
        "file_formats": list(file_formats),
        "created": datetime.now().strftime("%Y-%m-%dT%H:%M"),
        "lastest_change": None,
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
    json_file_path = add_to_json(json_file_path=json_file_path, entry=new_entry)

    return json_file_path


def generate_dataset_table(json_file_path: str):
    """
    Return two markdown strings:

    1. markdown_table – one summary table *per data_type*
    2. full_table     – one file-level table  per data_type
    ----------------------------------------------------------------
    The function preserves the original column layout.
    """

    if not os.path.exists(json_file_path):
        raise FileNotFoundError(f"The file {json_file_path} does not exist.")

    with open(json_file_path, "r", encoding="utf-8") as fh:
        data = json.load(fh)

    if not isinstance(data, list):
        raise TypeError("Expected a list of dataset objects inside the JSON file.")

    # ── group datasets by data_type ─────────────────────────────────
    grouped: dict[str, list[dict]] = defaultdict(list)
    for ds in data:
        dtype = ds.get("data_type", "Uncategorised")
        grouped[dtype].append(ds)

    # ── markdown builders ───────────────────────────────────────────
    summary_blocks = []   # concatenated into markdown_table
    detail_blocks  = []   # concatenated into full_table

    # column headers (same as in your original code)
    summary_header = (
        "| Name | Location | Created | Lastest Change | Hash "
        "| Provided | Run Command | Number of Files | Total Size (MB) "
        "| File Formats | Source | DOI | Citation | License | Notes |\n"
        "|------|----------|---------|---------------|------"
        "|---------|-------------|-----------------|---------------"
        "|--------------|--------|-----|----------|---------|-------|\n"
    )
    detail_header = (
        "| Name | Files | Location | Created | Lastest Change | Hash "
        "| Provided | File Size (MB) | Run Command | Source | DOI | "
        "Citation | License | Notes |\n"
        "|------|-------|----------|---------|---------------|------"
        "|----------|---------------|-------------|--------|-----|----------"
        "|---------|-------|\n"
    )

    # ── build tables per group ──────────────────────────────────────
    for dtype, entries in sorted(grouped.items()):
        # ---- summary table ----
        summary_blocks.append(f"### {dtype}\n")
        summary_blocks.append(summary_header)

        # ---- detail table ----
        need_detail = any(len(ds.get("data_files", [])) > 1 for ds in entries)
        if need_detail:
            detail_blocks.append(f"### {dtype}\n")
            detail_blocks.append(detail_header)

        for ds in entries:
            # ---------- common fields ----------
            data_name       = ds.get("data_name", "N/A")
            location        = ds.get("destination", "N/A")
            created         = ds.get("created", "N/A")
            last_change     = ds.get("lastest_change", "N/A")
            hash_           = ds.get("hash", "N/A")
            provided        = "Provided" if ds.get("data_files") else "Can be re-created"
            run_cmd         = ds.get("run_command", "N/A")
            n_files         = ds.get("number_of_files", 0)
            total_size_mb   = ds.get("total_size_mb", 0)
            file_formats    = "; ".join(ds.get("file_formats", ["Not available"]))
            source          = ds.get("source", "N/A")
            doi             = ds.get("DOI", "Not provided")
            citation        = ds.get("citation", "Not provided")
            license_        = ds.get("license", "Not provided")
            notes           = ds.get("notes", "")

            # ---------- summary row ----------
            summary_blocks.append(
                f"| {data_name} | {location} | {created} | {last_change} | {hash_} "
                f"| {provided} | {run_cmd} | {n_files} | {total_size_mb} | {file_formats} "
                f"| {source} | {doi} | {citation} | {license_} | {notes} |\n"
            )

            # ---------- detail rows ----------
            if need_detail:
                files  = ds.get("data_files", [])
                sizes  = ds.get("data_size",  [])
                # pad sizes list so zip doesn't truncate
                if len(sizes) < len(files):
                    sizes += ["?"] * (len(files) - len(sizes))

                for f, sz in zip(files, sizes):
                    detail_blocks.append(
                        f"| {data_name} | {f} | {location} | {created} | {last_change} | "
                        f"{hash_} | {provided} | {sz} | {run_cmd} | {source} | {doi} | "
                        f"{citation} | {license_} | {notes} |\n"
                    )

        # blank line between groups
        summary_blocks.append("\n")
        if need_detail:
            detail_blocks.append("\n")

    # join blocks into final markdown strings
    markdown_table = "".join(summary_blocks)
    full_table     = "".join(detail_blocks) if detail_blocks else ""

    return markdown_table, full_table

def generate_dataset_table_old(json_file_path):
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
        datasets = json.load(json_file)

    # If the data is a list, loop through each dataset entry
    if isinstance(datasets, list):
        markdown_table = (
            f"| Name             | Location        | Created         | Lastest Change  |Hash                       | Provided        | Run Command               | Number of Files | Total Size (MB) | File Formats         | Source          | DOI                | Citation               | License               | Notes                  |\n"
            f"|------------------|-----------------|-----------------|-----------------|---------------------------|-----------------|---------------------------|-----------------|-----------------|----------------------|-----------------|--------------------|------------------------|-----------------------|------------------------|\n"
        )

        full_table = (
            f"| Name             | Files                             | Location        | Created         | Lastest Change  | Hash                      | Provided        | File Size (MB) | Run Command               | Source           | DOI             | Citation               | License               | Notes                |\n"
            f"|------------------|-----------------------------------|-----------------|-----------------|-----------------|---------------------------|-----------------|----------------|---------------------------|------------------|-----------------|------------------------|-----------------------|----------------------|\n"
        )

        for entry in datasets:
            if isinstance(entry, dict):  # Only process dictionary entries
                # Extract required information from the JSON data
                data_name = entry.get("data_name", "N/A")
                data_files = " ; ".join(entry.get("data_files", ["Not available"]))  # Newline separated
                data_sizes = " ; ".join(str(size) for size in entry.get("data_size", ["Not available"]))
                created = entry.get("created", "N/A")
                lastest_change = entry.get("lastest_change", "N/A")
                location = entry.get("destination", "N/A")
                hash = entry.get("hash", "N/A")
                provided = "Provided" if entry.get("data_files") else "Can be re-created"
                run_command = entry.get("run_command", "N/A")
                number_of_files = entry.get("number_of_files", 0)
                total_size_mb = entry.get("total_size_mb", 0)
                file_formats = "; ".join(entry.get("file_formats", ["Not available"]))
                source = entry.get("source", "N/A")
                doi = entry.get("DOI", "Not provided")
                citation = entry.get("citation", "Not provided")
                license = entry.get("license", "Not provided")
                notes = entry.get("notes", "No additional notes")


                 # Format pdf table
                data_files = entry.get("data_files", ["Not available"])
                for file, size in zip(data_files, data_sizes):
                    full_table += (f"|{data_name}|{file}|{location}|{created}|{lastest_change}|{hash}|{provided}|{size}|{run_command}|{source}|{doi}|{citation}|{license}|{notes}|\n")

                # Format the markdown table for this entry
                markdown_table += (f"|{data_name}|{location}|{created}|{lastest_change}|{hash}|{provided}|{run_command}|{number_of_files}|{total_size_mb}|{file_formats}|{source}|{doi}|{citation}|{license}|{notes}|\n")
       
        return markdown_table,full_table
    else:
        # If the data is not a list, raise an error
        raise TypeError(f"Expected a list of datasets but got {type(datasets)}.")

def dataset_to_readme(markdown_table: str, readme_file: str = "./README.md"):
    """
    Updates or appends the '## Dataset List' section in the README file.

    Parameters:
        markdown_table (str): The markdown table to insert.
        readme_file (str): Path to the README file.
    """
    section_title = "**The following datasets are included in the project:**"

    new_dataset_section = f"{section_title}\n\n{markdown_table.strip()}\n"


    if not readme_file:
        readme_file = "README.md"
    
    readme_file= str(pathlib.Path(__file__).resolve().parent.parent.parent / pathlib.Path(readme_file))

    try:
        with open(readme_file, "r", encoding="utf-8") as f:
            readme_content = f.read()

        if section_title in readme_content:
            # Find the start and end of the existing section
            start = readme_content.find(section_title)
            end = readme_content.find("\n## ", start + len(section_title))
            if end == -1:
                end = len(readme_content)
            updated_content = readme_content[:start] + new_dataset_section + readme_content[end:]
        else:
            # Append the new section at the end
            updated_content = readme_content.strip() + "\n\n" + new_dataset_section

    except FileNotFoundError:
        # If the README doesn't exist, create it with the new section
        updated_content = new_dataset_section

    # Write the updated content to the README file
    with open(readme_file, "w", encoding="utf-8") as f:
        f.write(updated_content.strip())

    print(f"{readme_file} successfully updated with dataset section.")



@ensure_correct_kernel
def set_datasets(data_name:str= None, source:str=None, run_command:str=None, destination:str=None, doi:str = None,citation:str = None,license:str=None):
    
    def sanitize_folder_name(name):
        return name.replace(" ", "_").replace("/", "_").replace("\\", "_").replace(":", "_")
    
    def get_data_files(base_dir='./data', ignore=None, recursive=False):
        """
        Discover all data files under each subfolder of base_dir,
        skipping any directory or file in the ignore list.

        Args:
            base_dir (str): Root data directory containing subfolders.
            ignore (set[str] | None): Names to skip (folders or files).
            recursive (bool): If True, walk subdirectories recursively.

        Returns:
            list[str]: Full paths to all data files found.
        """
        if ignore is None:
            ignore = {'.git', '.gitignore', '.gitkeep', '.gitlog'}

        all_files = []
        # List only immediate subdirectories of base_dir
        try:
            subdirs = [
                name for name in os.listdir(base_dir)
                if os.path.isdir(os.path.join(base_dir, name))
                and name not in ignore
                and not name.startswith('.')
            ]
        except FileNotFoundError:
            return []

        for sub in sorted(subdirs):
            sub_path = os.path.join(base_dir, sub)
            if recursive:
                # Walk all nested files
                for root, dirs, files in os.walk(sub_path):
                    # prune ignored dirs
                    dirs[:] = [d for d in dirs if d not in ignore and not d.startswith('.')]
                    for fn in files:
                        if fn not in ignore and not fn.startswith('.'):
                            all_files.append(os.path.join(root, fn))
            else:
                # Only top-level files in this subfolder
                for fn in os.listdir(sub_path):
                    if fn in ignore or fn.startswith('.'):
                        continue
                    fp = os.path.join(sub_path, fn)
                    all_files.append(fp)

        return all_files

    json_file_path = None
    # If all input parameters are None, gather all files and folders from './data/00_raw/'
    if all(param is None for param in [data_name, source, run_command, destination, doi, citation, license]):
        data_files = get_data_files()
        for file in data_files:
            #json_file_path = set_dataset(data_name=os.path.basename(file), destination=file, source=None, run_command=None, json_file_path="./datasets.json", doi=None, citation=None, license=None)
            json_file_path = set_dataset(data_name=None, destination=file, source=None, run_command=None, json_file_path="./datasets.json", doi=None, citation=None, license=None) 
    else:
        if destination is None:
            destination = f"./data/00_raw/{sanitize_folder_name(data_name)}"
        json_file_path = set_dataset(data_name = data_name, destination = destination, source=source, run_command=run_command, json_file_path="./datasets.json", doi=doi, citation=citation, license=license)

    try:
        if json_file_path:
            markdown_table, full_table = generate_dataset_table(json_file_path)
            dataset_to_readme(markdown_table)
            dcas_readme = str(pathlib.Path(__file__).resolve().parent.parent.parent /  pathlib.Path("./DCAS template/dataset_list.md"))
            with open(dcas_readme, 'w') as markdown_file:
                markdown_file.write(full_table)
        else:
            print("No datasets were detected")
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
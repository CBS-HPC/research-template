import os
import json
import argparse
import subprocess
from datetime import datetime
import sys

def set_raw_data(data_name, remote_path, run_command, destination=None):
    """
    Executes a data download process and tracks created files in the specified path.

    Parameters:
        data_name (str): Name of the dataset.
        remote_path (str): The remote URL or path to the dataset.
        run_command (str): A command for executing the download function/script.
                           The script will ensure {remote_path} and {destination} are appended.
        destination (str): The path where the data will be stored. Defaults to './data/raw/data_name' if None.
    """
    
    def sanitize_folder_name(name):
        """
        Sanitizes the folder name to be filesystem compatible by removing or replacing invalid characters.
        
        Parameters:
            name (str): The folder name to be sanitized.
        
        Returns:
            str: A sanitized folder name.
        """
        # Replace invalid characters with underscores
        return name.replace(" ", "_").replace("/", "_").replace("\\", "_").replace(":", "_")
    
    def get_file_info(destination):
        """
        Get information about the files in the destination directory:
        - number of files
        - total size in MB
        - unique file formats (extensions)

        Parameters:
            destination (str): The path where the data is stored.

        Returns:
            tuple: (number_of_files, total_size_in_mb, file_formats)
        """
        # Get a list of files in the destination directory
        files = [f for f in os.listdir(destination) if os.path.isfile(os.path.join(destination, f))]

        # Count the number of files
        number_of_files = len(files)

        # Calculate the total size in MB
        total_size = sum(os.path.getsize(os.path.join(destination, f)) for f in files) / (1024 * 1024)

        # Extract file formats (extensions)
        file_formats = set(os.path.splitext(f)[1].lower() for f in files)

        return number_of_files, total_size, file_formats


    # Set default destination to './data/raw/data_name' if None
    if destination is None:
        destination = f"./data/raw/{sanitize_folder_name(data_name)}"
        # Define the output JSON file path
        json_file_path = f"./datasets.json"
    else:
        json_file_path = os.path.join(destination, f"{data_name}_metadata.json")
    

    # Ensure the destination directory exists
    os.makedirs(destination, exist_ok=True)

    # Get the initial list of files in the destination directory
    initial_files = set(os.listdir(destination))

    # Get the path of the current Python interpreter
    python_executable = sys.executable # FIX ME !!!

    # Prepare the command with the correct Python executable
    command_list = [python_executable, run_command, remote_path, destination]
    command_str = " ".join(command_list)

    try:
        # Execute the run_command
        result = subprocess.run(command_list, check=True, text=True, capture_output=True)
        print(f"Command output:\n{result.stdout}")
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {e}")
        print(f"Command output:\n{e.output}")
        return

    # Get the updated list of files in the destination directory
    updated_files = set(os.listdir(destination))
    
    # Determine the newly created files
    data_files = list(updated_files - initial_files)
    
    # Get the file statistics (number of files, total size, and file formats)
    number_of_files, total_size, file_formats = get_file_info(destination)

    # Create a JSON structure to store the information
    output = {
        "data_name": data_name,
        "remote_path": remote_path,
        "destination": destination,
        "run_command": " ".join([run_command, remote_path, destination]),
        "number_of_files": number_of_files,
        "total_size_mb": total_size,
        "file_formats": list(file_formats),
        "data_files": data_files,
        "timestamp": datetime.now().isoformat(),
    }
    
    # Write the JSON structure to the file
    with open(json_file_path, 'w') as json_file:
        json.dump(output, json_file, indent=4)
        
    print(f"Metadata saved to {json_file_path}")

    try:
        # Generate markdown table from the JSON file
        markdown_table = generate_markdown_table(json_file_path)
        
        print(markdown_table)
        # Append the table to the README
        append_to_readme(markdown_table)
        
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
    
    # Extract required information from the JSON data
    data_name = data.get("data_name", "N/A")
    data_files = "; ".join(data.get("data_files", ["Not available"]))
    location = data.get("destination", "N/A")
    provided = "TRUE" if data.get("data_files") else "FALSE"
    citation = data.get("citation", "N/A")
    
    # Format the markdown table
    markdown_table = (
        f"| Data.Name             | Data.Files                             | Location        | Provided | Citation              |\n"
        f"|-----------------------|----------------------------------------|-----------------|----------|-----------------------|\n"
        f"| {data_name}           | {data_files}                           | {location}      | {provided} | {citation}            |\n"
    )
    
    return markdown_table

def append_to_readme(markdown_table, readme_path:str= 'README.md'):
    """
    Appends the generated markdown table to the README file under the 
    'Data Availability and Provenance Statements' heading.

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
        if "Data Availability and Provenance Statements" in line:
            heading_found = True
            # Insert the markdown table below the heading
            content.insert(i + 1, markdown_table + "\n")
            break
    
    # If the heading is not found, add it at the end
    if not heading_found:
        content.append("\n# Data Availability and Provenance Statements\n")
        content.append(markdown_table + "\n")

    # Write the updated content back to the README
    with open(readme_path, 'w') as readme_file:
        readme_file.writelines(content)
    print(f"Appended data to {readme_path}")


if __name__ == "__main__":
    # Command-line argument parser
    parser = argparse.ArgumentParser(description="Set data source and monitor file creation.")
    parser.add_argument("data_name", help="Name of the dataset")
    parser.add_argument("remote_path", help="Remote URL or path to the dataset")
    parser.add_argument("run_command", help="Command for executing the download function/script")
    parser.add_argument("destination", nargs="?", default=None, help="Path where data will be stored (optional). Defaults to './data/raw/data_name'")
    
    args = parser.parse_args()

    # Execute the function with command-line arguments
    set_raw_data(args.data_name, args.remote_path, args.run_command, args.destination)

import os
import json
import argparse
import subprocess
from datetime import datetime



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
    
    # Set default destination to './data/raw/data_name' if None
    if destination is None:
        destination = f"./data/raw/{sanitize_folder_name(data_name)}"

    # Ensure the destination directory exists
    os.makedirs(destination, exist_ok=True)

    # Get the initial list of files in the destination directory
    initial_files = set(os.listdir(destination))
    
    # Ensure placeholders are included in the run_command
    if "{remote_path}" not in run_command:
        run_command += " {remote_path}"
    if "{destination}" not in run_command:
        run_command += " {destination}"
    
    # Replace placeholders in run_command
    command = run_command.format(remote_path=remote_path, destination=destination)
    print(f"Executing command: {command}")

    try:
        # Execute the run_command
        result = subprocess.run(command, shell=True, check=True, text=True, capture_output=True)
        print(f"Command output:\n{result.stdout}")
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {e}")
        print(f"Command output:\n{e.output}")
        return

    # Get the updated list of files in the destination directory
    updated_files = set(os.listdir(destination))
    
    # Determine the newly created files
    data_files = list(updated_files - initial_files)
    
    # Create a JSON structure to store the information
    output = {
        "data_name": data_name,
        "remote_path": remote_path,
        "destination": destination,
        "run_command": command,
        "timestamp": datetime.now().isoformat(),
        "data_files": data_files,
    }
    
    # Define the output JSON file path
    json_file_path = os.path.join(destination, f"{data_name}_metadata.json")
    
    # Write the JSON structure to the file
    with open(json_file_path, 'w') as json_file:
        json.dump(output, json_file, indent=4)
    
    print(f"Metadata saved to {json_file_path}")

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

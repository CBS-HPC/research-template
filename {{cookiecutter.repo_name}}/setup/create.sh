#!/bin/bash

# Get the repo_name and script paths passed from Python
repo_name=$1
version_control_path=$2
setup_remote_repository_path=$3

# Check if repo_name is provided (i.e., not None)
if [ "$repo_name" != "None" ]; then
    echo "Activating conda environment: $repo_name"
    # Activate conda environment only if repo_name is provided
    #source ~/anaconda3/etc/profile.d/conda.sh  # Adjust if using Miniconda or different installation path
    conda activate "$repo_name"                # Activate the environment with the name provided
else
    echo "No repo_name provided. Skipping conda environment activation."
fi

# Check if the script paths are provided and run them
if [ -f "$version_control_path" ]; then
    echo "Running version_control.py from $version_control_path..."
    python "$version_control_path"
else
    echo "Error: $version_control_path not found."
fi

if [ -f "$remote_repository_path" ]; then
    echo "Running remote_repository.py from $remote_repository_path..."
    python "$remote_repository_path"
else
    echo "Error: $remote_repository_path not found."
fi

echo "Environment setup completed successfully."

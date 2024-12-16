#!/bin/bash

# Get the repo_name, env_manager, and script paths passed from input
repo_name=$1
env_manager=$2
version_control_path=$3
remote_repository_path=$4

# Ensure the script runs on Linux/Mac
if [[ "$(uname -s)" != "Linux" && "$(uname -s)" != "Darwin" ]]; then
    echo "Error: This script is designed to run on Linux or MacOS only. Exiting."
    exit 1
fi

# Activate environment based on the environment manager
if [ "$repo_name" != "None" ]; then
    case "$env_manager" in
        "conda")
            echo "Activating Conda environment: $repo_name"
            # Adjust the source path to match your Conda installation
            source ~/anaconda3/etc/profile.d/conda.sh
            conda activate "$repo_name"
            ;;
        "venv")
            echo "Activating venv environment: $repo_name"
            venv_activate="./$repo_name/bin/activate"

            if [ -f "$venv_activate" ]; then
                echo "Activating venv using $venv_activate"
                source "$venv_activate"
            else
                echo "Error: venv activation script not found."
            fi
            ;;
        "virtualenv")
            echo "Activating virtualenv environment: $repo_name"
            virtualenv_activate="./$repo_name/bin/activate"

            if [ -f "$virtualenv_activate" ]; then
                echo "Activating virtualenv using $virtualenv_activate"
                source "$virtualenv_activate"
            else
                echo "Error: virtualenv activation script not found."
            fi
            ;;
        *)
            echo "Error: Unsupported environment manager '$env_manager'. Supported values are: Conda, venv, virtualenv."
            exit 1
            ;;
    esac
else
    echo "No repo_name provided. Skipping environment activation."
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
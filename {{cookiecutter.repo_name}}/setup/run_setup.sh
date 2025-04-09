#!/bin/bash

# Get the env_path, env_manager, and script paths passed from input
env_path=$1
env_manager=$2
version_control_path=$3
remote_repository_path=$4

# Activate environment based on the environment manager
if [ "$env_path" != "Base Installation" ] && [ "$env_manager" != "Base Installation" ]; then
    case "$env_manager" in
        "conda")
            echo "Activating Conda environment: $env_path"
            # Adjust the source path to match your Conda installation
            source ~/anaconda3/etc/profile.d/conda.sh
            conda activate "$env_path"
            ;;
        "venv")
            echo "Activating venv environment: $env_path"
            
            venv_activate="$env_path/bin/activate"

            if [ -f "$venv_activate" ]; then
                echo "Activating venv using $venv_activate"
                source "$venv_activate"
            else
                echo "Error: venv activation script not found."
            fi
            ;;
        "virtualenv")
            echo "Activating virtualenv environment: $env_path"
            
            virtualenv_activate="$env_path/bin/activate"

            if [ -f "$virtualenv_activate" ]; then
                echo "Activating virtualenv using $virtualenv_activate"
                source "$virtualenv_activate"
            else
                echo "Error: virtualenv activation script not found."
            fi
            ;;
        *)
            echo "Error: Unsupported environment manager '$env_manager'. Supported values are: Conda, venv, virtualenv."
            ;;
    esac
else
    echo "No valid env_path or env_manager provided. Skipping environment activation."
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
#!/bin/bash

# Get the env_path, env_manager, and script paths passed from input
env_path=$1
env_manager=$2
intro_path=$3
version_control_path=$4
remote_repository_path=$5
outro_path=$6

# Allow custom .env file path as first argument
envFile="${1:-.env}"

load_conda() {
    if [ -f "$envFile" ]; then
        while IFS='=' read -r key value; do
            if [[ ! "$key" =~ ^[[:space:]]*# && -n "$key" ]]; then
                key=$(echo "$key" | xargs)
                value=$(echo "$value" | xargs | sed 's/^"\(.*\)"$/\1/')

                # If CONDA path, resolve it to an absolute path
                if [[ "$key" == "CONDA" ]]; then
                    # Resolve relative to the script's directory
                    script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
                    abs_value="$(realpath -m "$script_dir/$value")"
                    export CONDA="$abs_value"
                    echo "Resolved CONDA path: $CONDA"
                fi
            fi
        done < "$envFile"
    else
        echo "Warning: $envFile not found"
    fi
}



# Activate environment based on the environment manager
if [ "$env_path" != "Base Installation" ] && [ "$env_manager" != "Base Installation" ]; then
    case "$env_manager" in
        "conda")
            echo "Activating Conda environment: $env_path"
            

            script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
            cd "$script_dir"
            echo "0"
            load_conda
            echo "1"
            # Activate Conda environment
            if [ -n "$CONDA" ]; then
                echo "2"
                eval "$($CONDA/conda shell.bash hook)"
                echo "3"
                conda activate "$env_path"
                echo "4"
                echo "Conda environment $env_path is active"
            else
                echo "Error: conda script not found."
            fi

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

if [ -f "$intro_path" ]; then
    echo "Running intro.py from $intro_path..."
    python "$intro_path"
else
    echo "Error: $intro_path not found."
fi

if [ -f "$version_control_path" ]; then
    echo "Running versioning_setup.py from $version_control_path..."
    python "$version_control_path"
else
    echo "Error: $version_control_path not found."
fi

if [ -f "$remote_repository_path" ]; then
    echo "Running repo_setup.py from $remote_repository_path..."
    python "$remote_repository_path"
else
    echo "Error: $remote_repository_path not found."
fi

if [ -f "$outro_path" ]; then
    echo "Running outro.py from $outro_path..."
    python "$outro_path"
else
    echo "Error: $outro_path not found."
fi

echo "Environment setup completed successfully."
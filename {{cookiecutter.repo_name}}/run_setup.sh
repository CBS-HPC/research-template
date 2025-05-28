#!/bin/bash

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$script_dir"


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
    local conda_path=""

    if [ -f "$envFile" ]; then
        while IFS='=' read -r key value; do
            # Skip comments and empty keys
            [[ "$key" =~ ^[[:space:]]*# ]] && continue
            [[ -z "$key" ]] && continue

            key=$(echo "$key" | xargs)
            value=$(echo "$value" | xargs | sed 's/^"\(.*\)"$/\1/')

            if [[ "$key" == "CONDA" ]]; then
                conda_path=$(realpath "$value")
                if [ -x "$conda_path/conda" ]; then
                    export CONDA="$conda_path"
                    echo "Resolved and exported CONDA: $CONDA"
                else
                    echo "Warning: conda binary not found at $conda_path/conda" >&2
                fi
            fi
        done < "$envFile"
    else
        echo "Warning: $envFile not found" >&2
    fi
}

# Activate environment based on the environment manager
if [ "$env_path" != "Base Installation" ] && [ "$env_manager" != "Base Installation" ]; then
    case "$env_manager" in
        "conda")
            load_conda
            CONDA_ENV_PATH=$(realpath "$env_path")
            
            if [ -n "$CONDA_ENV_PATH" ] && [ -n "$CONDA" ]; then    
                echo "Activating Conda environment at $CONDA_ENV_PATH"
                eval "$($CONDA/conda shell.bash hook)"
                conda activate "$CONDA_ENV_PATH"
            else
                echo "Error: conda script not found."
            fi

            ;;
        "venv")           

            VENV_ENV_PATH=$(realpath "$env_path")    
            if [ -n "$VENV_ENV_PATH" ]; then
                VENV_ENV_PATH=$(realpath "$env_path")
                echo "Activating Venv environment at $VENV_ENV_PATH"
                source "$VENV_ENV_PATH/bin/activate"
            else
                echo "Error: venv activation script not found."
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
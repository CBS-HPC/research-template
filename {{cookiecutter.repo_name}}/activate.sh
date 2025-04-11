#!/bin/bash

# Allow custom .env file path as first argument
envFile="${1:-.env}"

# Function to load environment variables from .env file
load_env() {
    if [ -f "$envFile" ]; then
        # Read the .env file line by line
        while IFS='=' read -r key value; do
            # Ignore empty lines and comments
            if [[ ! "$key" =~ ^[[:space:]]*# && -n "$key" ]]; then
                # Remove leading/trailing whitespace and quotes
                key=$(echo "$key" | xargs)
                value=$(echo "$value" | xargs | sed 's/^"\(.*\)"$/\1/')

                # Handle specific keys for absolute paths
                if [[ "$key" == "VENV_ENV_PATH" || "$key" == "CONDA_ENV_PATH" || "$key" == "CONDA" || "$key" == "GH" ]]; then
                    abs_value=$(realpath "$value")
                    export "$key"="$abs_value"
                    echo "Loaded $key as absolute path: $abs_value"

                elif [ -d "$value" ]; then
                    # Add directory to PATH
                    abs_path=$(realpath "$value")
                    export PATH="$abs_path:$PATH"
                    echo "Added $key to PATH ($abs_path)"

                elif [ -x "$value" ]; then
                    # If it's an executable file, add its directory to PATH
                    abs_path=$(realpath "$value")
                    bin_dir=$(dirname "$abs_path")
                    export PATH="$bin_dir:$PATH"
                    echo "Added $key (executable) to PATH ($bin_dir)"

                else
                    # Set normal environment variable
                    export "$key"="$value"
                    echo "Loaded variable: $key=$value"
                fi
            fi
        done < "$envFile"
        echo "Environment variables loaded from $envFile"
    else
        echo "Warning: $envFile not found"
    fi
}

# Load environment variables from .env file
load_env

# Activate Conda environment
if [ -n "$CONDA_ENV_PATH" ] && [ -n "$CONDA" ]; then
    echo "Activating Conda environment at $CONDA_ENV_PATH"
    eval "$($CONDA/conda shell.bash hook)"
    conda activate "$CONDA_ENV_PATH"
fi

# Activate virtual environment if defined in the .env file
if [ -n "$VENV_ENV_PATH" ]; then
    echo "Activating virtual environment at $VENV_ENV_PATH"
    source "$VENV_ENV_PATH/bin/activate"
fi

# FIX ME !!!! NEED TO LOAD ALL PATHs from .env after VENV or CONDA
# Ensure the gh binary is in the PATH (after activating the virtual environment)
if [ -n "$GH" ]; then
    export PATH="$GH:$PATH"
    echo "Added GH directory to PATH: $GH"
fi

# Set prompt to reflect current repo and environment name
repo_name=$(basename "$PWD")
env_label=$(basename "$VENV_ENV_PATH" 2>/dev/null || basename "$CONDA_ENV_PATH" 2>/dev/null)
export PS1="[$repo_name:$env_label] \$ "

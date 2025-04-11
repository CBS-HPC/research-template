#!/bin/bash

# Path to .env file
envFile=".env"

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
                if [ "$key" == "VENV_ENV_PATH" ] || [ "$key" == "CONDA_ENV_PATH" ] || [ "$key" == "CONDA" ]; then
                    # Convert the value to an absolute path if it's a relative path
                    abs_value=$(realpath "$value")
                    export "$key"="$abs_value"
                    echo "Loaded $key as absolute path: $abs_value"
                elif [ -d "$value" ]; then
                    # Convert relative paths to absolute and add to PATH
                    abs_path=$(realpath "$value")
                    export PATH="$abs_path:$PATH"
                    echo "Added $key to PATH ($abs_path)"
                else
                    # Set the environment variable normally
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

# Load environment variables from .env first
load_env

# Activate Conda environment if defined in the .env file
if [ -n "$CONDA_ENV_PATH" ] && [ -n "$CONDA" ]; then
    echo "Activating Conda environment at $CONDA_ENV_PATH"
    eval "$($CONDA/conda shell.bash hook)"
    conda init
    echo "conda activate $CONDA_ENV_PATH" >> ~/.bashrc
fi

# Activate virtual environment if defined in the .env file
if [ -n "$VENV_ENV_PATH" ]; then
    echo "Activating virtual environment at $VENV_ENV_PATH"
    source "$VENV_ENV_PATH/bin/activate"
fi

# Change prompt to reflect environment name (if desired)
repo_name=$(basename "$PWD")  # Get the current directory name as the repo name
export PS1="[$repo_name] \$ "

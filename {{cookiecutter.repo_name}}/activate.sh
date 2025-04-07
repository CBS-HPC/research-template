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

                # Check if value is a valid directory path and add to PATH
                if [ -d "$value" ]; then
                    export PATH="$value:$PATH"
                    echo "Added $key to PATH"
                else
                    # Otherwise, set the environment variable
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

# Activate Conda environment if defined in the .env file
if [ -n "$CONDA_ENV_PATH" ]; then
    echo "Activating Conda environment at $CONDA_ENV_PATH"
    conda activate "$CONDA_ENV_PATH"
fi

# Activate virtual environment if defined in the .env file
if [ -n "$VENV_PATH" ]; then
    echo "Activating virtual environment at $VENV_PATH"
    source "$VENV_PATH/bin/activate"
fi

# Load environment variables from .env
load_env

# Change prompt to reflect environment name (if desired)
repo_name=$(basename "$PWD")  # Get the current directory name as the repo name
export PS1="[$repo_name] \$ "

#!/bin/bash

# Path to .env file (same as the one used in activate.sh)
envFile=".env"

# Deactivate the Conda environment if it was activated
if [ -n "$CONDA_ENV_PATH" ]; then
    echo "Deactivating Conda environment"
    conda deactivate
fi

# Deactivate the venv if it was activated
if [ -n "$VENV_PATH" ]; then
    echo "Deactivating virtual environment"
    deactivate
fi

# Remove the environment variables set during activation
if [ -f "$envFile" ]; then
    # Read the .env file line by line
    while IFS='=' read -r key value; do
        # Ignore empty lines and comments
        if [[ ! "$key" =~ ^[[:space:]]*# && -n "$key" ]]; then
            # Remove leading/trailing whitespace and quotes
            key=$(echo "$key" | xargs)
            value=$(echo "$value" | xargs | sed 's/^"\(.*\)"$/\1/')

            # Remove the environment variable if it exists
            if [ -n "${!key}" ]; then
                unset "$key"
                echo "Removed environment variable: $key"
            fi

            # If the variable was a path that was added to the PATH, remove it
            if [ "$key" == "PATH" ]; then
                # Remove the path from the PATH environment variable
                PATH=$(echo "$PATH" | sed "s;$value;;g")
                export PATH
                echo "Removed path: $value from PATH"
            fi
        fi
    done < "$envFile"
    echo "Environment variables removed from $envFile"
else
    echo "Warning: $envFile not found"
fi

# Reset the prompt to the default state
export PS1="\$ "

echo "Deactivation of $(basename "$PWD") is complete."
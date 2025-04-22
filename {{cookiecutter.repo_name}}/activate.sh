#!/bin/bash

# Allow custom .env file path as first argument
envFile="${1:-.env}"

activate_env() {
    if [ -f "$envFile" ]; then
        while IFS='=' read -r key value; do
            if [[ ! "$key" =~ ^[[:space:]]*# && -n "$key" ]]; then
                key=$(echo "$key" | xargs)
                value=$(echo "$value" | xargs | sed 's/^"\(.*\)"$/\1/')

                if [[ "$key" == "VENV_ENV_PATH" || "$key" == "CONDA_ENV_PATH" || "$key" == "CONDA" ]]; then
                    abs_value=$(realpath "$value")
                    export "$key"="$abs_value"
                    echo "Loaded $key as absolute path: $abs_value"
                fi
            fi
        done < "$envFile"
    else
        echo "Warning: $envFile not found"
    fi
}

load_env() {
    if [ -f "$envFile" ]; then
        while IFS='=' read -r key value; do
            if [[ ! "$key" =~ ^[[:space:]]*# && -n "$key" ]]; then
                key=$(echo "$key" | xargs)
                value=$(echo "$value" | xargs | sed 's/^"\(.*\)"$/\1/')

                if [[ "$key" != "VENV_ENV_PATH" && "$key" != "CONDA_ENV_PATH" && "$key" != "CONDA" ]]; then
                    if [ -d "$value" ]; then
                        abs_path=$(realpath "$value")
                        export PATH="$abs_path:$PATH"
                        echo "Added $key to PATH ($abs_path)"
                    elif [ -x "$value" ]; then
                        abs_path=$(realpath "$value")
                        bin_dir=$(dirname "$abs_path")
                        export PATH="$bin_dir:$PATH"
                        echo "Added $key (executable) to PATH ($bin_dir)"
                    else
                        export "$key"="$value"
                        echo "Loaded variable: $key=$value"
                    fi
                fi
            fi
        done < "$envFile"
        echo "Environment variables loaded from $envFile"
    else
        echo "Warning: $envFile not found"
    fi
}

verify_env_paths() {
    echo ""
    echo "Verifying paths from $envFile..."

    local missing_paths=0

    while IFS='=' read -r key value; do
        if [[ ! "$key" =~ ^[[:space:]]*# && -n "$key" ]]; then
            key=$(echo "$key" | xargs)
            value=$(echo "$value" | xargs | sed 's/^"\(.*\)"$/\1/')

            # Check if the value appears to be a path
            if [[ "$value" == /* || "$value" == ./* ]]; then
                if [ ! -e "$value" ]; then
                    echo "❌ Missing path for $key: $value"
                    missing_paths=1
                fi
            fi
        fi
    done < "$envFile"

    if [[ $missing_paths -eq 1 ]]; then
        echo ""
        echo "⚠️ Some paths are missing. Run 'install-dependencies' to re-install the project."
    else
        echo "✅ All required paths exist."
    fi
}

# Load VENV and CONDA variables
activate_env

# Activate Conda environment
if [ -n "$CONDA_ENV_PATH" ] && [ -n "$CONDA" ]; then
    echo "Activating Conda environment at $CONDA_ENV_PATH"
    eval "$($CONDA/conda shell.bash hook)"
    conda activate "$CONDA_ENV_PATH"
fi

# Activate virtual environment if defined
if [ -n "$VENV_ENV_PATH" ]; then
    echo "Activating virtual environment at $VENV_ENV_PATH"
    source "$VENV_ENV_PATH/bin/activate"
fi

# Load the rest of the environment
load_env

# Set prompt
repo_name=$(basename "$PWD")
env_label=$(basename "$VENV_ENV_PATH" 2>/dev/null || basename "$CONDA_ENV_PATH" 2>/dev/null)
export PS1="[$repo_name:$env_label] \$ "

# check missing paths
verify_env_paths
#!/bin/bash


# Allow custom .env file path as first argument
envFile="${1:-.env}"

reset_env() {
    unset CONDA_ENV_PATH
    unset CONDA
    unset VENV_ENV_PATH
    unset "$CONDA_ENV_PATH"
    unset "$CONDA"
    unset "$VENV_ENV_PATH"
    # Optionally reset other environment variables like PATH if necessary
    export PATH=$(echo $PATH | sed -e 's/:\/.*conda.*//g' -e 's/:\/.*venv.*//g') # Removes paths related to conda or venv
}

activate_env() {
    if [ -f "$envFile" ]; then
        while IFS='=' read -r key value; do
            if [[ ! "$key" =~ ^[[:space:]]*# && -n "$key" ]]; then
                key=$(echo "$key" | xargs)
                value=$(echo "$value" | xargs | sed 's/^"\(.*\)"$/\1/')
                if [[ "$key" == "VENV_ENV_PATH" || "$key" == "CONDA_ENV_PATH" ]]; then
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

activate_env

# Deactivate Conda environment if it was activated
if [ -n "$CONDA_ENV_PATH" ]; then
    echo "Deactivating Conda environment"
    conda deactivate
fi

# Deactivate the virtual environment if it was activated
if [ -n "$VENV_ENV_PATH" ]; then
    echo "Deactivating virtual environment"
    deactivate
fi

reset_env 

# Remove the environment variables and PATH additions from .env
if [ -f "$envFile" ]; then
    while IFS='=' read -r key value; do
        if [[ ! "$key" =~ ^[[:space:]]*# && -n "$key" ]]; then
            key=$(echo "$key" | xargs)
            value=$(echo "$value" | xargs | sed 's/^"\(.*\)"$/\1/')

            # Unset the variable if it was set
            if [ -n "${!key}" ]; then
                unset "$key"
                echo "Removed environment variable: $key"
            fi

            # If this variable pointed to a directory or executable, clean from PATH
            if [ -d "$value" ] || [ -x "$value" ]; then
                abs_path=$(realpath "$value")
                PATH=$(echo "$PATH" | tr ':' '\n' | grep -vFx "$abs_path" | paste -sd ':' -)
                bin_dir=$(dirname "$abs_path")
                PATH=$(echo "$PATH" | tr ':' '\n' | grep -vFx "$bin_dir" | paste -sd ':' -)
                export PATH
                echo "Removed $abs_path and $bin_dir from PATH (if present)"
            fi
        fi
    done < "$envFile"
    echo "Environment cleanup from $envFile complete."
else
    echo "Warning: $envFile not found"
fi


# Reset prompt
export PS1="\$ "

echo "Deactivation of $(basename "$PWD") is complete."
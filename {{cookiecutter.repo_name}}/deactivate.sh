#!/bin/bash

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$script_dir"

# Allow custom .env file path as first argument
envFile="${1:-.env}"

reset_env() {
    unset CONDA_ENV_PATH
    unset CONDA
    unset VENV_ENV_PATH

    if [ -n "$ORIGINAL_PATH" ]; then
        export PATH="$ORIGINAL_PATH"
        echo "PATH restored to original."
    else
        # Fallback if ORIGINAL_PATH is not set
        export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
        echo "PATH reset to default minimal system paths."
    fi
}

load_env_paths() {
    if [ -f "$envFile" ]; then
        while IFS='=' read -r key value; do
            if [[ ! "$key" =~ ^[[:space:]]*# && -n "$key" ]]; then
                key=$(echo "$key" | xargs)
                value=$(echo "$value" | xargs | sed 's/^"\(.*\)"$/\1/')

                case "$key" in
                    VENV_ENV_PATH)
                        export VENV_ENV_PATH=$(realpath "$value")
                        ;;
                    CONDA_ENV_PATH)
                        export CONDA_ENV_PATH=$(realpath "$value")
                        ;;
                    CONDA)
                        export CONDA=$(realpath "$value")
                        ;;
                esac
            fi
        done < "$envFile"
    else
        echo "Warning: $envFile not found"
    fi
}

# Load paths to deactivate correctly
load_env_paths

# Deactivate Conda environment if active
if [ -n "$CONDA_ENV_PATH" ] && command -v conda >/dev/null 2>&1; then
    echo "Deactivating Conda environment"
    conda deactivate
fi

# Deactivate Python venv if active
if [ -n "$VENV_ENV_PATH" ] && type deactivate >/dev/null 2>&1; then
    echo "Deactivating virtual environment"
    deactivate
fi

# Reset tracked environment variables
reset_env

# Remove additional PATH entries and env vars from .env
if [ -f "$envFile" ]; then
    while IFS='=' read -r key value; do
        if [[ ! "$key" =~ ^[[:space:]]*# && -n "$key" ]]; then
            key=$(echo "$key" | xargs)
            value=$(echo "$value" | xargs | sed 's/^"\(.*\)"$/\1/')

            # Unset custom environment variables (but not core ones again)
            if [[ "$key" != "VENV_ENV_PATH" && "$key" != "CONDA_ENV_PATH" && "$key" != "CONDA" ]]; then
                if [ -n "${!key}" ]; then
                    unset "$key"
                    echo "Removed environment variable: $key"
                fi

                # Clean absolute paths from PATH
                if [ -d "$value" ] || [ -x "$value" ]; then
                    abs_path=$(realpath "$value")
                    PATH=$(echo "$PATH" | tr ':' '\n' | grep -vFx "$abs_path" | paste -sd ':' -)
                    bin_dir=$(dirname "$abs_path")
                    PATH=$(echo "$PATH" | tr ':' '\n' | grep -vFx "$bin_dir" | paste -sd ':' -)
                    export PATH
                    echo "Removed $abs_path and $bin_dir from PATH (if present)"
                fi
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

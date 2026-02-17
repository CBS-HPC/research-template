#!/bin/bash

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$script_dir"

# Allow custom .env file path as first argument
envFile="${1:-.env}"

# Save original PATH once, before activation
if [ -z "$ORIGINAL_PATH" ]; then
    export ORIGINAL_PATH="$PATH"
    echo "Saved ORIGINAL_PATH."
fi

reset_env() {
    unset CONDA_ENV_PATH
    unset CONDA
    unset VENV_ENV_PATH

    if [ -n "$ORIGINAL_PATH" ]; then
        export PATH="$ORIGINAL_PATH"
        echo "PATH restored to original."
    else
        export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
        echo "PATH reset to default minimal system paths."
    fi
}

activate_env() {
    local venv_path=""
    local conda_path=""
    local conda_bin=""

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
        echo "Warning: $envFile not found" >&2
    fi
}

load_env() {
    prepend_path_first() {
        local target="$1"
        [ -z "$target" ] && return 1
        local cleaned=""
        local oldIFS="$IFS"
        IFS=':'
        for p in $PATH; do
            [ -z "$p" ] && continue
            if [ "$p" != "$target" ]; then
                if [ -z "$cleaned" ]; then
                    cleaned="$p"
                else
                    cleaned="$cleaned:$p"
                fi
            fi
        done
        IFS="$oldIFS"
        if [ -n "$cleaned" ]; then
            export PATH="$target:$cleaned"
        else
            export PATH="$target"
        fi
        return 0
    }

    if [ -f "$envFile" ]; then
        while IFS='=' read -r key value; do
            if [[ ! "$key" =~ ^[[:space:]]*# && -n "$key" ]]; then
                key=$(echo "$key" | xargs)
                value=$(echo "$value" | xargs | sed 's/^"\(.*\)"$/\1/')

                if [[ "$key" != "VENV_ENV_PATH" && "$key" != "CONDA_ENV_PATH" && "$key" != "CONDA" ]]; then
                    if [ -d "$value" ]; then
                        abs_path=$(realpath "$value")
                        prepend_path_first "$abs_path"
                        echo "Prioritized $key in PATH ($abs_path)"
                    elif [ -x "$value" ]; then
                        abs_path=$(realpath "$value")
                        bin_dir=$(dirname "$abs_path")
                        prepend_path_first "$bin_dir"
                        echo "Prioritized $key (executable) in PATH ($bin_dir)"
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

reset_env
activate_env

# Now use the local vars
if [ -n "$CONDA_ENV_PATH" ] && [ -n "$CONDA" ]; then
    echo "Activating Conda environment at $CONDA_ENV_PATH"
    eval "$($CONDA/conda shell.bash hook)"
    conda activate "$CONDA_ENV_PATH"
fi

if [ -n "$VENV_ENV_PATH" ]; then
    echo "Activating Venv environment at $VENV_ENV_PATH"
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

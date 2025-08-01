#!/bin/bash

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$script_dir"

# Get the env_path, env_manager, and script paths passed from input
env_path=$1
env_manager=$2
main_setup=$3

# Allow custom .env file path as first argument
envFile=".env" 

load_conda() {
    local conda_path=""

    if [ -f "$envFile" ]; then
        while IFS='=' read -r key value; do
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
if [ "$env_manager" != "" ]; then
    case "$env_manager" in
        "conda")
            load_conda
            CONDA_ENV_PATH=$(realpath "$env_path")
            if [ -n "$CONDA_ENV_PATH" ] && [ -n "$CONDA" ]; then    
                echo "Activating Conda environment at $CONDA_ENV_PATH"
                eval "$($CONDA/conda shell.bash hook)"
                conda activate "$CONDA_ENV_PATH"

                # Cleanup: remove .venv folder and uv.lock file if they exist
                if [ -d ".venv" ]; then
                    echo "Removing .venv directory..."
                    rm -rf .venv
                fi
                
                if [ -f "uv.lock" ]; then
                    echo "Removing uv.lock file..."
                    rm -f uv.lock
                fi
                if ! command -v uv &>/dev/null; then
                    pip install uv
                fi

                uv pip install --upgrade uv pip setuptools wheel python-dotenv
            else
                echo "Error: conda script not found."
            fi
            ;;
        "venv")           
            VENV_ENV_PATH=$(realpath "$env_path")    
            if [ -n "$VENV_ENV_PATH" ]; then
                echo "Activating Venv environment at $VENV_ENV_PATH"
                source "$VENV_ENV_PATH/bin/activate"

                if [ ! -d ".venv" ]; then
                    if ! command -v uv &>/dev/null; then
                        pip install uv
                    fi
                    uv lock
                    uv add --upgrade uv pip setuptools wheel python-dotenv 
                fi  # <-- this was missing
            else
                echo "Error: venv activation script not found."
            fi
            ;;
        *)
            echo "No valid env_path or env_manager provided. Using system Python."
            ;;
    esac
else
    echo "No valid env_path or env_manager provided. Using system Python."
fi

# -------------------------------
# Run the main Python script
# -------------------------------
if [ -f "$main_setup" ]; then
    python "$main_setup"
else
    echo "Error: $main_setup not found."
fi

echo ""
echo "Environment setup completed successfully."

#!/bin/bash

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$script_dir"

# Get the env_path, env_manager, and script paths passed from input
env_path=$1
env_manager=$2
main_setup=$3

# Allow custom .env file path as first argument
envFile=".env" 


# -------- helpers --------
# Remove a path but NEVER fail the script if the removal errors out.
safe_rm_path() {
    # usage: safe_rm_path "<path>"
    # works for files or directories; errors are downgraded to warnings.
    local target="$1"
    # -f makes file removal non-erroring if missing; -r handles directories.
    # If rm still errors (e.g., permissions), swallow it and continue.
    rm -rf -- "$target" 2>/dev/null || {
        echo "Warning: could not remove '$target'; continuing." >&2
        return 0
    }
}

# -------------------------

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
                
                if command -v uv >/dev/null 2>&1; then
                    python -m pip uninstall -y uv >/dev/null 2>&1 || \
                    pip uninstall -y uv >/dev/null 2>&1 || true
                fi

                echo "Activating Conda environment at $CONDA_ENV_PATH"
                eval "$($CONDA/conda shell.bash hook)"
                conda activate "$CONDA_ENV_PATH"

                # Cleanup: remove .venv folder and uv.lock file if they exist
                if [ -d ".venv" ]; then
                    echo "Removing .venv directory..."
                    safe_rm_path ".venv"
                fi
                
                if [ -f "uv.lock" ]; then
                    echo "Removing uv.lock file..."
                    safe_rm_path uv.lock
                fi
                if ! command -v uv &>/dev/null; then
                    pip install uv
                fi

                uv pip install --upgrade python-dotenv pathspec
                #uv pip install --upgrade uv pip setuptools wheel python-dotenv pathspec
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
                    uv add --upgrade uv pip setuptools wheel python-dotenv pathspec
                fi
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

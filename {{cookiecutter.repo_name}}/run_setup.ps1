param (
    [string]$env_path,
    [string]$env_manager,  # "conda" or "venv" 
    [string]$main_setup    # Path to the main Python script
)

# Keep native path separators; avoid rewriting with '/'
# $env_path = $env_path -replace '\\', '/'

$venvPath  = ".venv"
$uvLockFile = "uv.lock"

# ---------- helper: safe removal ----------
function Remove-PathSafe {
    [CmdletBinding()]
    param([Parameter(Mandatory)][string]$Path)
    try {
        if (Test-Path -LiteralPath $Path) {
            Remove-Item -LiteralPath $Path -Recurse -Force -ErrorAction Stop
            Write-Verbose "Removed '$Path'."
        }
    } catch {
        Write-Warning "Could not remove '$Path'. Continuing. $($_.Exception.Message)"
    }
}
# -----------------------------------------

# ---------- how to run (conda run / uv run / python) ----------
function Run-PythonScript {
    param (
        [string]$script_path,
        [string]$label
    )

    if (-not (Test-Path $script_path)) {
        Write-Output "Error: $label not found at $script_path"
        exit 1
    }

    switch ($env_manager.ToLower()) {
        "conda" {
            # Use conda run to pin to the exact env (name or path)
            $condaArgs = if (Test-Path -LiteralPath $env_path) { @('-p', $env_path) } else { @('-n', $env_path) }
            Write-Output "Running via: conda run $($condaArgs -join ' ') python `"$script_path`""
            conda run @condaArgs --no-capture-output python "$script_path"
            if ($LASTEXITCODE) { exit $LASTEXITCODE }
        }
        "venv" {
            # Use uv run so PATH/VS Code state can't hijack Python
            if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
                Write-Output "Error: 'uv' not found on PATH. Install it first (e.g., 'python -m pip install uv')."
                exit 1
            }
            Write-Output "Running via: uv run python `"$script_path`""
            uv run python "$script_path"
            if ($LASTEXITCODE) { exit $LASTEXITCODE }
        }
        default {
            Write-Output "Running via system python: `"$script_path`""
            python "$script_path"
            if ($LASTEXITCODE) { exit $LASTEXITCODE }
        }
    }
}
# -------------------------------------------------------------

# Activate/prepare the Python environment (only what’s needed)
if ($env_manager -ne "") {
    switch ($env_manager.ToLower()) {

        "conda" {
            Write-Output "Activating Conda environment (not required when using 'conda run'): $env_path"
            conda activate $env_path

            # Clean up project venv artifacts so they can't hijack PATH/VS Code
            Write-Output "Removing .venv directory (if present)..."
            Remove-PathSafe -Path $venvPath
            Write-Output "Removing uv.lock file (if present)..."
            Remove-PathSafe -Path $uvLockFile

            # Ensure tools live in the conda env (pinned with conda run)
            $condaArgs = if (Test-Path -LiteralPath $env_path) { @('-p', $env_path) } else { @('-n', $env_path) }

            # 1) Make sure base build tooling is present (inside the target Conda env)
            conda run @condaArgs --no-capture-output python -m pip install -U pip setuptools wheel

            # 2) Install uv into that Conda env
            conda run @condaArgs --no-capture-output python -m pip install -U uv

            # (optional) sanity check
            conda run @condaArgs --no-capture-output uv --version

            # 3) Now use uv *inside that env* to install your packages
            conda run @condaArgs --no-capture-output uv pip install --upgrade python-dotenv pathspec nbformat
            
            if ($LASTEXITCODE) { exit $LASTEXITCODE }
        }

        "venv" {
            Write-Output "Activating venv: $env_path"
            $activateScript = Join-Path $env_path "Scripts\Activate.ps1"
            if (Test-Path $activateScript) {
                & $activateScript
            } else {
                Write-Output "Cannot find activate script at $activateScript"
                exit 1
            }

            # Make sure 'uv' exists in the active venv
            if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
                python -m pip install uv
                if ($LASTEXITCODE) { exit $LASTEXITCODE }
            }

            # Bootstrap or upgrade via uv (project-level)
            if (-not (Test-Path $venvPath)) {
                uv lock
                if ($LASTEXITCODE) { exit $LASTEXITCODE }
                uv add --upgrade pip setuptools wheel python-dotenv pathspec nbformat
                if ($LASTEXITCODE) { exit $LASTEXITCODE }
            } else {
                uv pip install --upgrade pip setuptools wheel python-dotenv pathspec nbformat
                if ($LASTEXITCODE) { exit $LASTEXITCODE }
            }
        }

        default {
            Write-Output "Unknown env_manager. Proceeding without activation."
        }
    }
} else {
    Write-Output "Using system Python (no environment activation)."
}

# Run the main Python script through the selected runner
Run-PythonScript -script_path $main_setup -label "main setup script"

Write-Output ""
Write-Output "Environment setup completed successfully."

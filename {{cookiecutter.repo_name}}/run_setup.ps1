param (
    [string]$env_path,
    [string]$env_manager,  # "conda", "venv", or "base Installation"
    [string]$main_setup    # Path to the main Python script
)

$env_path = $env_path -replace '\\', '/'

# Define $venvPath and $uvLockFile here, accessible for both cases
$venvPath = ".venv"
$uvLockFile = "uv.lock"

# Activate the Python environment
if ($env_manager -ne "base Installation") {
    switch ($env_manager.ToLower()) {
        "conda" {
            Write-Output "Activating Conda environment: $env_path"
            conda activate $env_path

            # Remove .venv folder and uv.lock file if they exist
            if (Test-Path $venvPath) {
                Write-Output "Removing $venvPath..."
                Remove-Item -Recurse -Force $venvPath
            }

            if (Test-Path $uvLockFile) {
                Write-Output "Removing $uvLockFile..."
                Remove-Item -Force $uvLockFile
            }
            if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
                pip install uv
            }

            uv pip install --upgrade uv pip setuptools wheel
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

            if (-not (Test-Path $venvPath)) {
                # Check if 'uv' is available
                if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
                    pip install uv
                }
                uv lock
                uv add --upgrade uv pip setuptools wheel
            }
        }
        default {
            Write-Output "Unknown env_manager. Proceeding without activation."
        }
    }
} else {
    Write-Output "Using system Python (no environment activation)."
}

# Run the main Python script
function Run-PythonScript {
    param (
        [string]$script_path,
        [string]$label
    )
    if (Test-Path $script_path) {
        Write-Output ""
        Write-Output "Running $label from $script_path..."
        python "$script_path"
    } else {
        Write-Output "Error: $label not found at $script_path"
    }
}

Run-PythonScript -script_path $main_setup -label "main setup script"

Write-Output ""
Write-Output "Environment setup completed successfully."

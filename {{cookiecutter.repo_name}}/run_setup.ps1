# PowerShell script to set up environment and run specified Python scripts

param (
    [string]$env_path,
    [string]$env_manager,  # Environment manager: Conda, venv
    [string]$main_setup
)

$env_path = $env_path -replace '\\', '/'

# Default to system Python
$pythonExe = "python"

# Resolve Python executable based on environment manager
if ($env_manager -ne "base Installation") {
    switch ($env_manager.ToLower()) {
        "conda" {
            Write-Output "Activating Conda environment: $env_path"
            conda activate $env_path
            # Let conda handle the path — assume global python updated
        }
        "venv" {
            Write-Output "Using Python from venv: $env_path"
            $pythonExe = Join-Path $env_path "Scripts\python.exe"
        }
        default {
            Write-Output "No valid env_path or env_manager provided. Using system Python.2"
        }
    }
} else {
    Write-Output "No valid env_path or env_manager provided. Using system Python."
}

# Helper function to run Python scripts
function Run-PythonScript {
    param (
        [string]$script_path,
        [string]$label
    )
    if (Test-Path $script_path) {
        Write-Output "Running $label from $script_path..."
        & "$pythonExe" "$script_path"
    } else {
        Write-Output "Error: $label not found at $script_path"
    }
}

# Run Python scripts
Run-PythonScript -script_path $main_setup -label "main setup script"


Write-Output "Environment setup completed successfully."

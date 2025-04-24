# PowerShell script to set up environment and run specified Python scripts

# Get parameters passed from PowerShell
param (
    [string]$env_path,
    [string]$env_manager,  # Environment manager: Conda, venv, or virtualenv
    [string]$intro_path,
    [string]$version_control_path,
    [string]$remote_repository_path,
    [string]$outro_path
)

# Activate environment based on the environment manager
if ($env_path -ne "Base Installation" -and $env_manager -ne "Base Installation") {

    $env_path = $env_path -replace '\\', '/'

    switch ($env_manager.ToLower()) {
        "conda" {
            Write-Output "Activating Conda environment: $env_path"
            conda activate $env_path
        }
        "venv" {
            Write-Output "Activating venv environment: $env_path"

            $venv_activate = "$env_path/Scripts/activate"

            if (Test-Path $venv_activate) {
                Write-Output "Activating venv using $venv_activate"
                & $venv_activate
            } else {
                Write-Output "Error: venv activation script not found : $venv_activate"
            }
        }
        "virtualenv" {
            Write-Output "Activating virtualenv environment: $env_path"

            $virtualenv_activate = "$env_path/Scripts/activate"

            if (Test-Path $virtualenv_activate) {
                Write-Output "Activating virtualenv using $virtualenv_activate"
                & $virtualenv_activate
            } else {
                Write-Output "Error: virtualenv activation script not found: $virtualenv_activate"
            }
        }
        default {
            Write-Output "Error: Unsupported environment manager '$env_manager'. Supported values are: Conda, venv, virtualenv."
        }
    }
} else {
    Write-Output "No valid repo_name or env_manager provided. Skipping environment activation."
}

# Check if the script paths are provided and run them
if (Test-Path $intro_path) {
    Write-Output "Running intro.py from $intro_path..."
    python $intro_path
} else {
    Write-Output "Error: $intro_path not found."
}

if (Test-Path $version_control_path) {
    Write-Output "Running versioning_setup.py from $version_control_path..."
    python $version_control_path
} else {
    Write-Output "Error: $version_control_path not found."
}

if (Test-Path $remote_repository_path) {
    Write-Output "Running repo_setup.py from $remote_repository_path..."
    python $remote_repository_path
} else {
    Write-Output "Error: $remote_repository_path not found."
}

if (Test-Path $outro_path) {
    Write-Output "Running outro.py from $outro_path..."
    python $outro_path
} else {
    Write-Output "Error: $outro_path not found."
}

Write-Output "Environment setup completed successfully."
# Deactivation script for {{ cookiecutter.repo_name }}

# Change directory to the script's folder to handle relative paths properly
Set-Location -Path $PSScriptRoot

# Path to .env file
$envFile = ".\.env"

# Function to get a variable's value from the .env file
function Get-EnvValueFromDotEnv {
    param (
        [string]$varName,
        [string]$envFile = ".\.env"
    )

    if (Test-Path $envFile) {
        $line = Get-Content $envFile | Where-Object { $_ -match "^\s*$varName\s*=\s*(.+)$" }
        if ($line -match "^\s*$varName\s*=\s*(.+)$") {
            return $matches[1].Trim('"')
        }
    }
    return $null
}

$condaEnvPath   = Get-EnvValueFromDotEnv -varName "CONDA_ENV_PATH"
$venvEnvPath    = Get-EnvValueFromDotEnv -varName "VENV_ENV_PATH"

# Informational messages
if ($condaEnvPath) {
    Write-Output "Deactivating Conda environment"
    if (Get-Command conda -ErrorAction SilentlyContinue) {
        conda deactivate
    }
}

# venv deactivate call safety
if ($venvEnvPath) {
    Write-Output "Deactivating virtual environment"
    if (Get-Command deactivate -ErrorAction SilentlyContinue) {
        deactivate
    } else {
        Write-Warning "No 'deactivate' command found for virtual environment."
    }
}

# Restore original PATH if saved
if ($env:ORIGINAL_PATH) {
    $env:PATH = $env:ORIGINAL_PATH
    Remove-Item Env:ORIGINAL_PATH -ErrorAction SilentlyContinue
    Write-Host "Restored original PATH."
} else {
    Write-Warning "Original PATH was not saved. PATH not restored."
}

# Remove environment variables loaded from .env
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match "^\s*([^#][^=]+?)\s*=\s*(.+)$") {
            $key = $matches[1].Trim()

            # Always unset the environment variable
            if (Test-Path "Env:$key") {
                Remove-Item -Path "Env:$key" -ErrorAction SilentlyContinue
                Write-Host "Removed environment variable: $key"
            }
        }
    }
    Write-Output "Environment variables from .env cleaned up."
} else {
    Write-Warning ".env file not found. Skipping environment variable cleanup."
}

# Reset prompt
function global:prompt {
    return "PS $($executionContext.SessionState.Path.CurrentLocation)> "
}

Write-Output "Deactivation of '{{ cookiecutter.repo_name }}' is complete."

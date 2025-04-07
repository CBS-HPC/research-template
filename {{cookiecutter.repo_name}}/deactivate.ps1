# Path to .env file (same as the one used in activate.ps1)
$envFile = ".\.env"

# Deactivate the Conda environment if it was activated
if ($env:CONDA_ENV_PATH) {
    Write-Output "Deactivating Conda environment"
    conda deactivate
}

# Deactivate the venv if it was activated
if ($env:VENV_PATH) {
    Write-Output "Deactivating virtual environment"
    deactivate
}

# Remove the environment variables set during activation
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match "^\s*([^#][^=]+?)\s*=\s*(.+)$") {
            $key = $matches[1].Trim()

            # Remove the environment variable if it exists
            if ($env:$key) {
                Remove-Item -Path "Env:$key"
                Write-Host "Removed environment variable: $key"
            }

            # If the variable was a path that was added to the PATH, remove it
            if ($key -eq 'PATH') {
                $env:PATH = ($env:PATH -split ";") | Where-Object { $_ -ne $matches[2].Trim('"') } -join ";"
                Write-Host "Removed path: $($matches[2].Trim('"')) from PATH"
            }
        }
    }
    Write-Output "Environment variables removed from .env"
} else {
    Write-Warning ".env file not found"
}

# Reset the prompt to the default state
function global:prompt {
    return "PS $($executionContext.SessionState.Path.CurrentLocation)> "
}

Write-Output "Deactivation of {{ cookiecutter.repo_name }} is complete."


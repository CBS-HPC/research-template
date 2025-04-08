# Path to .env file
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
            $value = $matches[2].Trim()

            # Remove quotes around values (both single and double quotes)
            $value = $value.Trim('"').Trim("'")

            # If the variable is PATH, remove the path that was added
            if (Test-Path $value) {
                # Split the PATH by semicolon, remove the path, and join again
                $env:PATH = (($env:PATH -split ";") | Where-Object { $_ -ne $value }) -join ";"
                Write-Host "Removed path: $value from PATH"
            } else {
                # Remove the environment variable if it exists
                Remove-Item -Path "Env:$key" -ErrorAction SilentlyContinue
                Write-Host "Removed environment variable: $key"
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

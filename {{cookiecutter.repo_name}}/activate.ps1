# Path to .env file
$envFile = ".\.env"

# Load variables from .env
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match "^\s*([^#][^=]+?)\s*=\s*(.+)$") {
            $key = $matches[1].Trim()
            $value = $matches[2].Trim('"')  # Remove quotes if present
            
            # Check if the value is a valid directory path
            if (Test-Path $value) {
                # If the value is a valid path, add it to the PATH environment variable
                $env:PATH = $value + ";" + $env:PATH
                Write-Host "Added $value to PATH"
            } else {
                # Otherwise, set the environment variable
                Set-Item -Path "Env:$key" -Value $value
                Write-Host "Loaded variable: $key = $value"
            }
        }
    }
    Write-Output "Environment variables loaded from .env"
} else {
    Write-Warning ".env file not found"
}

# Check if a Conda environment is defined in the .env
if ($env:CONDA_ENV_PATH) {
    Write-Output "Activating Conda environment at $env:CONDA_ENV_PATH"
    conda activate $env:CONDA_ENV_PATH
}

# Check if a venv path is defined in the .env
if ($env:VENV_PATH) {
    Write-Output "Activating virtual environment at $env:VENV_PATH"
    . "$env:VENV_PATH\Scripts\Activate.ps1"
}

# Optional: Change prompt to reflect env name
function global:prompt {
    return "[{{ cookiecutter.repo_name }}] PS $($executionContext.SessionState.Path.CurrentLocation)> "
}

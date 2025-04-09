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
                Write-Host "Added $key to PATH"
            } else {
                # Otherwise, set the environment variable
                Set-Item -Path "Env:$key" -Value $value
                Write-Host "Loaded variable: $key"
            }
        }
    }
    Write-Output "Environment variables loaded from .env"
} else {
    Write-Warning ".env file not found"
}

# Helper function to get value from .env file
function Get-EnvValueFromDotEnv {
    param (
        [string]$varName,
        [string]$envFile = ".\.env"
    )

    # Check if the .env file exists
    if (Test-Path $envFile) {
        $line = Get-Content $envFile | Where-Object { $_ -match "^\s*$varName\s*=\s*(.+)$" }
        if ($line -match "^\s*$varName\s*=\s*(.+)$") {
            return $matches[1].Trim('"')
        }
    }

    return $null
}

# Check if a Conda environment is defined in the .env
$condaEnvPath = Get-EnvValueFromDotEnv -varName "CONDA_ENV_PATH"
if ($condaEnvPath) {
    Write-Output "Activating Conda environment at $condaEnvPath"
    conda activate $condaEnvPath
}

# Check if a venv path is defined in the .env
$venvPath = Get-EnvValueFromDotEnv -varName "VENV_ENV_PATH"
if ($venvPath) {
    Write-Output "Activating virtual environment at $venvPath"
    . "$venvPath\Scripts\Activate.ps1"
}

# Optional: Change prompt to reflect env name
function global:prompt {
    return "[{{ cookiecutter.repo_name }}] PS $($executionContext.SessionState.Path.CurrentLocation)> "
}

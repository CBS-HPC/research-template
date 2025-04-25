# Deactivation script for {{ cookiecutter.repo_name }}

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
    conda deactivate
}

if ($venvEnvPath) {
    Write-Output "Deactivating virtual environment"
    deactivate 
}

# Helper function to clean a value from PATH
function Remove-FromPath {
    param (
        [string]$target
    )
    $cleaned = ($env:PATH -split ";" | Where-Object { $_ -and ($_ -ne $target) }) -join ";"
    $env:PATH = $cleaned
}

# Remove the environment variables set during activation
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match "^\s*([^#][^=]+?)\s*=\s*(.+)$") {
            $key = $matches[1].Trim()
            $value = $matches[2].Trim().Trim('"').Trim("'")

            try {
                $resolved = Resolve-Path -Path $value -ErrorAction Stop
                $resolvedPath = $resolved.Path
                if ($env:PATH -split ";" | Where-Object { $_ -eq $resolvedPath }) {
                    Remove-FromPath -target $resolvedPath
                    Write-Host "Removed $resolvedPath from PATH"
                }
            } catch {
                # Skip if path resolution fails (non-path value)
            }

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

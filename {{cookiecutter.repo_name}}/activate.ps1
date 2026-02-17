
# Change directory to the script's folder to handle relative paths properly
Set-Location -Path $PSScriptRoot

# Path to .env file
$envFile = ".\.env"

# Save original PATH if not already saved
if (-not $env:ORIGINAL_PATH) {
    $env:ORIGINAL_PATH = $env:PATH
    Write-Host "Saved ORIGINAL_PATH"
}

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

function Set-PathFirst {
    param (
        [Parameter(Mandatory = $true)]
        [string]$PathEntry
    )

    $resolvedEntry = (Resolve-Path -Path $PathEntry -ErrorAction SilentlyContinue)
    if (-not $resolvedEntry) {
        return $false
    }
    $entry = $resolvedEntry.Path

    $parts = @()
    if ($env:PATH) {
        $parts = $env:PATH -split ';' | Where-Object { $_ -and $_.Trim() -ne "" }
    }

    # Remove existing occurrences (case-insensitive), then prepend.
    $filtered = @($parts | Where-Object { $_.TrimEnd('\') -ine $entry.TrimEnd('\') })
    $env:PATH = (@($entry) + $filtered) -join ';'
    return $true
}

function Verify-EnvPaths {
    param (
        [string]$envFile = ".\.env"
    )

    Write-Host ""
    Write-Host "Verifying paths from $envFile..." -ForegroundColor Cyan

    $missingPaths = $false

    if (Test-Path $envFile) {
        Get-Content $envFile | ForEach-Object {
            if ($_ -match "^\s*([^#][^=]+?)\s*=\s*(.+)$") {
                $key = $matches[1].Trim()
                $value = $matches[2].Trim()
                $value = $value.Trim('"')
                $value = $value.Trim("'")

                # Check if it looks like a path
                if ($value -match '^(?:\.\\|\.\/|\.\.\\|\.\.\/|\/|[a-zA-Z]:\\)') {
                    if (-not (Test-Path $value)) {
                        Write-Host "Missing path for $key : $value" -ForegroundColor Red
                        $missingPaths = $true 
                    }
                }
            }
        }

        if ($missingPaths) {
            Write-Host ""
            Write-Host "Some paths are missing. Run 'install-dependencies' to re-install the project." -ForegroundColor Yellow
        } else {
            Write-Host "All required paths exist." -ForegroundColor Green
        }
    } else {
        Write-Warning "$envFile not found"
    }
}

# --- First: Load only environment activation paths (venv or conda) ---
$condaPath      = Get-EnvValueFromDotEnv -varName "CONDA"
$condaEnvPath   = Get-EnvValueFromDotEnv -varName "CONDA_ENV_PATH"
$venvEnvPath    = Get-EnvValueFromDotEnv -varName "VENV_ENV_PATH"

if ($condaEnvPath -and $condaPath) {
    Write-Output "Activating Conda environment at $condaEnvPath"
    $resolvedCondaPath = Resolve-Path -Path $condaPath | Select-Object -ExpandProperty Path

    if ($resolvedCondaPath) {
        # Check if it ends in "Library\bin"
        if ($resolvedCondaPath -like "*\Library\bin") {
            # Move up two levels to reach root Conda directory
            $condaPath = Split-Path (Split-Path $resolvedCondaPath)
        } else {
            $condaPath = $resolvedCondaPath
        }

        & "$condaPath\shell\condabin\conda-hook.ps1"
        conda activate "$condaEnvPath"
    }
}

if ($venvEnvPath) {
    Write-Output "Activating virtual environment at $venvEnvPath"
    . "$venvEnvPath\Scripts\Activate.ps1"
}

# --- Then: Load all other variables ---
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match "^\s*([^#][^=]+?)\s*=\s*(.+)$") {
            $key = $matches[1].Trim()
            $value = $matches[2].Trim('"')

            # Skip variables already handled
            if ($key -notin @("VENV_ENV_PATH", "CONDA_ENV_PATH", "CONDA")) {
                if (Test-Path $value) {
                    $resolved = (Resolve-Path -Path $value).Path
                    $pathToAdd = $resolved
                    if (-not (Get-Item -Path $resolved).PSIsContainer) {
                        $pathToAdd = Split-Path -Path $resolved -Parent
                    }
                    if (Set-PathFirst -PathEntry $pathToAdd) {
                        Write-Host "Prioritized $key in PATH: $pathToAdd"
                    }
                }
            }
        }
    }
} else {
    Write-Warning ".env file not found"
}

# --- Optional: Customize prompt ---
function global:prompt {
    return "[{{ cookiecutter.repo_name }}] PS $($executionContext.SessionState.Path.CurrentLocation)> "
}

# check missing paths
Verify-EnvPaths

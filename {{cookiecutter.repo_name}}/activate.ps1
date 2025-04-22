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
                        Write-Host "❌ Missing path for $key : $value" -ForegroundColor Red
                        $missingPaths = $true 
                    }
                }
            }
        }

        if ($missingPaths) {
            Write-Host ""
            Write-Host "⚠️  Some paths are missing. Run 'install-dependencies' to re-install the project." -ForegroundColor Yellow
        } else {
            Write-Host "✅ All required paths exist." -ForegroundColor Green
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
    $rawCondaPath = Resolve-Path -Path $condaPath


    if ($rawCondaPath) {
        # Normalize and resolve the full path
        $resolvedCondaPath = Resolve-Path -Path $rawCondaPath | Select-Object -ExpandProperty Path
    
        # Check if it ends in "Library\bin"
        if ($resolvedCondaPath -like "*\Library\bin") {
            # Move up two levels to reach root Conda directory
            $condaPath = Split-Path (Split-Path $resolvedCondaPath)
            Write-Warning "⚠️  CONDA path appears to be inside 'Library\\bin'. Adjusting to root path: $condaPath"
        } else {
            $condaPath = $resolvedCondaPath
        }
    
    }

    & "$condaPath\shell\condabin\conda-hook.ps1"
    conda activate "$condaEnvPath"
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
                    # Add path to PATH
                    $resolved = Resolve-Path -Path $value
                    $env:PATH = "$resolved;$env:PATH"
                    Write-Host "Added $key to PATH: $resolved"
                } else {
                    # Set regular environment variable
                    Set-Item -Path "Env:$key" -Value $value
                    Write-Host "Loaded variable: $key"
                }
            }
        }
    }
    Write-Output "Remaining environment variables loaded from .env"
} else {
    Write-Warning ".env file not found"
}

# --- Optional: Customize prompt ---
function global:prompt {
    return "[{{ cookiecutter.repo_name }}] PS $($executionContext.SessionState.Path.CurrentLocation)> "
}

# check missing paths
Verify-EnvPaths
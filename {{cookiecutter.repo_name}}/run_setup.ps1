param (
    [string]$env_path,
    [string]$env_manager,  # "conda" or "venv" 
    [string]$main_setup    # Path to the main Python script
)

$env_path = $env_path -replace '\\', '/'

# Define $venvPath and $uvLockFile here, accessible for both cases
$venvPath = ".venv"
$uvLockFile = "uv.lock"

# ---------- helper: safe removal ----------
function Remove-PathSafe {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string]$Path
    )
    try {
        if (Test-Path -LiteralPath $Path) {
            # -LiteralPath avoids wildcard surprises
            Remove-Item -LiteralPath $Path -Recurse -Force -ErrorAction Stop
            Write-Verbose "Removed '$Path'."
        }
    }
    catch {
        Write-Warning "Could not remove '$Path'. Continuing. $($_.Exception.Message)"
        # swallow the error so the script never stops on removal failures
    }
}
# -----------------------------------------



# Activate the Python environment
if ($env_manager -ne "") {
    switch ($env_manager.ToLower()) {
        "conda" {
            # Uninstall uv if currently on PATH
            if (Get-Command uv -ErrorAction SilentlyContinue) {
                try { python -m pip uninstall -y uv | Out-Null } catch {}
            }
            
            Write-Output "Activating Conda environment: $env_path"
            conda activate $env_path
            
            # Remove .venv folder and uv.lock file (non-fatal if removal fails)
            Write-Output "Removing .venv directory (if present)..."
            Remove-PathSafe -Path $venvPath

            Write-Output "Removing uv.lock file (if present)..."
            Remove-PathSafe -Path $uvLockFile


            if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
                pip install uv
            }

            uv pip install --upgrade uv pip setuptools wheel python-dotenv pathspec
        }
        "venv" {
            Write-Output "Activating venv: $env_path"
            $activateScript = Join-Path $env_path "Scripts\Activate.ps1"
            if (Test-Path $activateScript) {
                & $activateScript
            } else {
                Write-Output "Cannot find activate script at $activateScript"
                exit 1
            }

            if (-not (Test-Path $venvPath)) {
                # Check if 'uv' is available
                if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
                    pip install uv
                }
                uv lock
                uv add --upgrade uv pip setuptools wheel python-dotenv pathspec
            }
        }
        default {
            Write-Output "Unknown env_manager. Proceeding without activation."
        }
    }
} else {
    Write-Output "Using system Python (no environment activation)."
}

# Run the main Python script
function Run-PythonScript {
    param (
        [string]$script_path,
        [string]$label
    )
    if (Test-Path $script_path) {
        python "$script_path"
    } else {
        Write-Output "Error: $label not found at $script_path"
    }
}

Run-PythonScript -script_path $main_setup -label "main setup script"

Write-Output ""
Write-Output "Environment setup completed successfully."

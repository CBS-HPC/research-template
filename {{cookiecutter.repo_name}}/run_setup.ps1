param (
    [string]$env_path,
    [string]$env_manager,  # "conda", "venv", or "base Installation"
    [string]$main_setup    # Path to the main Python script
)

$env_path = $env_path -replace '\\', '/'

# -------------------------------
# 🧪 Activate the Python Environment
# -------------------------------
if ($env_manager -ne "base Installation") {
    switch ($env_manager.ToLower()) {
        "conda" {
            Write-Output "Activating Conda environment: $env_path"
            conda activate $env_path
        }
        "venv" {
            Write-Output "Activating venv: $env_path"
            $activateScript = Join-Path $env_path "Scripts\Activate.ps1"
            if (Test-Path $activateScript) {
                & $activateScript
            } else {
                Write-Output "❌ Cannot find activate script at $activateScript"
                exit 1
            }
        }
        default {
            Write-Output "⚠️ Unknown env_manager. Proceeding without activation."
        }
    }
} else {
    Write-Output "Using system Python (no environment activation)."
}

# -------------------------------
# 📦 Install and Upgrade Tools
# -------------------------------
Write-Output "`n📦 Installing or upgrading 'uv'..."
pip install --upgrade uv

Write-Output "`n🚀 Upgrading pip, setuptools, and wheel using uv..."
uv pip install --upgrade pip setuptools wheel

# -------------------------------
# ▶️ Run the Main Python Script
# -------------------------------
function Run-PythonScript {
    param (
        [string]$script_path,
        [string]$label
    )
    if (Test-Path $script_path) {
        Write-Output "`n▶️ Running $label from $script_path..."
        python "$script_path"
    } else {
        Write-Output "❌ Error: $label not found at $script_path"
    }
}

Run-PythonScript -script_path $main_setup -label "main setup script"

Write-Output "`n✅ Environment setup completed successfully."

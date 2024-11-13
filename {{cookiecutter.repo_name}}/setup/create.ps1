# PowerShell script to set up environment and run specified Python scripts

# Get parameters passed from PowerShell
param (
    [string]$repo_name,
    [string]$setup_version_control_path,
    [string]$setup_remote_repository_path
)

# Check if repo_name is provided (i.e., not None)
if ($repo_name -ne "None") {
    Write-Output "Activating conda environment: $repo_name"
    
    # Directly activate the environment by name
    conda activate $repo_name
} else {
    Write-Output "No repo_name provided. Skipping conda environment activation."
}

# Check if the script paths are provided and run them
if (Test-Path $setup_version_control_path) {
    Write-Output "Running setup_version_control.py from $setup_version_control_path..."
    python $setup_version_control_path
} else {
    Write-Output "Error: $setup_version_control_path not found."
}

if (Test-Path $setup_remote_repository_path) {
    Write-Output "Running setup_remote_repository.py from $setup_remote_repository_path..."
    python $setup_remote_repository_path
} else {
    Write-Output "Error: $setup_remote_repository_path not found."
}

Write-Output "Environment setup completed successfully."

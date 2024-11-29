# List of applications to check in .env
$apps = @()

# Check for specific folders and adjust the $apps list
if (Test-Path ".datalad") {
    $apps = @("GIT", "CONDA", "GH", "GLAB", "GIT-ANNEX", "DATALAD", "RCLONE", "GIT-ANNEX-REMOTE-RCLONE")
}
elseif (Test-Path ".dvc") {
    $apps = @("GIT", "CONDA", "GH", "GLAB", "DVC")
}
elseif (Test-Path ".git") {
    $apps = @("GIT", "CONDA", "GH", "GLAB")
}
else {
    $apps = @("CONDA")
}

# Check if the .env file exists in the current folder
if (Test-Path ".env") {
    Write-Host ".env file found."

    # Iterate over the list of applications
    foreach ($app in $apps) {
        # Use Select-String to check if the line for the app exists
        $line = Select-String -Path ".env" -Pattern "^$app="
        if ($line) {
            # Extract the value and set it as an environment variable
            $value = $line.Line.Split('=')[1].Trim('"')
	    $value = [System.IO.Path]::GetDirectoryName($value)
	    $env:PATH = "$value;$env:PATH"
            
            # Dynamically set the environment variable for the current session
            $envVariableName = "env:" + $app
            Set-Item -Path $envVariableName -Value $value

            # Set the environment variable persistently for the user (for future sessions)
            [System.Environment]::SetEnvironmentVariable($app, $value, [System.EnvironmentVariableTarget]::User)
        }
        else {
            Write-Host "$app not found in .env."
        }
    }

    # Check if Conda is in the path
    if (-not (Get-Command "conda" -ErrorAction SilentlyContinue)) {
        Write-Host "Conda is not found in the path. Please ensure Conda is installed and in the path."
        exit 1
    }
    else {
        Write-Host "Conda is available in the path."
    }

    # Attempt to activate the Conda environment
    $folderName = (Get-Item -LiteralPath ".").Name
    try {
        Write-Host "Attempting to activate Conda environment '$folderName'..."
        conda activate $folderName
    }
    catch {
        Write-Host "Failed to activate Conda environment '$folderName'."

        # Check if environment.yml exists and create the environment
        if (Test-Path "environment.yml") {
            Write-Host "Found environment.yml. Creating Conda environment..."
            conda env create -f environment.yml
            Write-Host "Conda environment created. Activating..."
            conda activate $folderName
        }
        else {
            Write-Host "No Conda environment named '$folderName' and no environment.yml found."
        }
    }
}
else {
    Write-Host "No .env file found in the current folder."
    exit 1
}

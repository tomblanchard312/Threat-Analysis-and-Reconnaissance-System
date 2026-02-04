# Install portable Node.js to USB drive
param(
    [string]$TargetDrive = "L:"
)

Write-Host "Installing portable Node.js to $TargetDrive\nodejs" -ForegroundColor Cyan

$nodeVersion = "v20.11.0"
$nodeUrl = "https://nodejs.org/dist/$nodeVersion/node-$nodeVersion-win-x64.zip"
$nodeZip = "$env:TEMP\nodejs.zip"
$targetDir = "$TargetDrive\nodejs"

# Create target directory
if (-not (Test-Path $targetDir)) {
    New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
    Write-Host "Created: $targetDir"
}

# Download
Write-Host "Downloading Node.js $nodeVersion (~30MB)..."
try {
    Invoke-WebRequest -Uri $nodeUrl -OutFile $nodeZip -UseBasicParsing
    Write-Host "Download complete"
} catch {
    Write-Host "ERROR: Download failed - $_" -ForegroundColor Red
    exit 1
}

# Extract
Write-Host "Extracting..."
try {
    Expand-Archive -Path $nodeZip -DestinationPath "$env:TEMP\nodejs_temp" -Force

    # Move contents from nested folder
    $extractedFolder = Get-ChildItem "$env:TEMP\nodejs_temp" -Directory | Select-Object -First 1
    if ($extractedFolder) {
        Copy-Item "$($extractedFolder.FullName)\*" $targetDir -Recurse -Force
        Write-Host "Extracted to: $targetDir"
    }

    # Cleanup
    Remove-Item $nodeZip -Force -ErrorAction SilentlyContinue
    Remove-Item "$env:TEMP\nodejs_temp" -Recurse -Force -ErrorAction SilentlyContinue
} catch {
    Write-Host "ERROR: Extraction failed - $_" -ForegroundColor Red
    exit 1
}

# Verify
if (Test-Path "$targetDir\node.exe") {
    $version = & "$targetDir\node.exe" --version
    Write-Host ""
    Write-Host "SUCCESS: Node.js $version installed!" -ForegroundColor Green
    Write-Host "Location: $targetDir" -ForegroundColor Green
    Write-Host ""
    Write-Host "MCP servers will now be available when running from USB." -ForegroundColor Cyan
} else {
    Write-Host "ERROR: node.exe not found after extraction" -ForegroundColor Red
    exit 1
}

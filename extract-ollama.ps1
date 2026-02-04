# Extract and install downloaded Ollama
$tempZip = "C:\Users\sirra\AppData\Local\Temp\ollama-new.zip"
$tempExtract = "C:\Users\sirra\AppData\Local\Temp\ollama-extract"
$TargetDir = "L:\Ollama"

Write-Host "Extracting Ollama..."
if (Test-Path $tempExtract) {
    Remove-Item $tempExtract -Recurse -Force
}
Expand-Archive -Path $tempZip -DestinationPath $tempExtract -Force
Write-Host "  Extracted"

# Backup existing
if (Test-Path "$TargetDir\ollama.exe") {
    Write-Host "  Backing up existing ollama.exe..."
    Copy-Item "$TargetDir\ollama.exe" "$TargetDir\ollama.exe.bak" -Force
}

# Copy new files
Write-Host "  Copying to $TargetDir..."
Copy-Item "$tempExtract\*" $TargetDir -Recurse -Force
Write-Host "  Done"

# Verify
Write-Host ""
$ver = & "$TargetDir\ollama.exe" --version 2>&1
Write-Host "New version: $ver"

# Test launch
Write-Host ""
Write-Host "Testing 'ollama launch --help'..."
& "$TargetDir\ollama.exe" launch --help 2>&1

# Cleanup
Remove-Item $tempZip -Force -ErrorAction SilentlyContinue
Remove-Item $tempExtract -Recurse -Force -ErrorAction SilentlyContinue
Write-Host ""
Write-Host "Update complete!"

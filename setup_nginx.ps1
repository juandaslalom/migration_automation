# ============================================================
# Download, install, and configure Nginx as a reverse proxy
# for the Migration Automation Streamlit app.
# Run this script as Administrator.
# ============================================================

Param(
    [string]$NginxVersion = "1.27.4",
    [string]$InstallDir   = "E:\nginx"
)

$ErrorActionPreference = "Stop"

$zipUrl  = "https://nginx.org/download/nginx-$NginxVersion.zip"
$zipFile = "$env:TEMP\nginx-$NginxVersion.zip"

# --- Download ---
if (-not (Test-Path "$InstallDir\nginx.exe")) {
    Write-Host "[*] Downloading Nginx $NginxVersion ..."
    Invoke-WebRequest -Uri $zipUrl -OutFile $zipFile -UseBasicParsing

    Write-Host "[*] Extracting to $InstallDir ..."
    Expand-Archive -Path $zipFile -DestinationPath $env:TEMP -Force

    # Move extracted folder to install dir
    $extracted = Join-Path $env:TEMP "nginx-$NginxVersion"
    if (Test-Path $InstallDir) { Remove-Item $InstallDir -Recurse -Force }
    Move-Item -Path $extracted -Destination $InstallDir
    Remove-Item $zipFile -Force

    Write-Host "[+] Nginx installed at $InstallDir" -ForegroundColor Green
} else {
    Write-Host "[=] Nginx already installed at $InstallDir"
}

# --- Copy config ---
$projectConf = Join-Path $PSScriptRoot "nginx.conf"
$nginxConf   = Join-Path $InstallDir "conf\nginx.conf"

Write-Host "[*] Copying nginx.conf -> $nginxConf"
Copy-Item -Path $projectConf -Destination $nginxConf -Force

# --- Stop existing Nginx (if running) ---
$running = Get-Process -Name "nginx" -ErrorAction SilentlyContinue
if ($running) {
    Write-Host "[*] Stopping existing Nginx process ..."
    Push-Location $InstallDir
    & .\nginx.exe -s quit 2>$null
    Start-Sleep -Seconds 2
    # Force kill if still running
    Get-Process -Name "nginx" -ErrorAction SilentlyContinue | Stop-Process -Force
    Pop-Location
}

# --- Start Nginx ---
Write-Host "[*] Starting Nginx ..."
Push-Location $InstallDir
Start-Process -FilePath ".\nginx.exe" -WindowStyle Hidden
Pop-Location

Start-Sleep -Seconds 1
$proc = Get-Process -Name "nginx" -ErrorAction SilentlyContinue
if ($proc) {
    Write-Host ""
    Write-Host "Nginx is running!" -ForegroundColor Green
    Write-Host "  Listening on  : http://0.0.0.0:80"
    Write-Host "  Proxying to   : http://127.0.0.1:8501 (Streamlit)"
    Write-Host "  IP whitelist  : see nginx.conf geo block"
    Write-Host ""
    Write-Host "Management commands (run from $InstallDir):"
    Write-Host "  Stop   : .\nginx.exe -s quit"
    Write-Host "  Reload : .\nginx.exe -s reload"
    Write-Host "  Test   : .\nginx.exe -t"
} else {
    Write-Host "ERROR: Nginx failed to start. Check $InstallDir\logs\error.log" -ForegroundColor Red
}

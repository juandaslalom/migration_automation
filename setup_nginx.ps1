# ============================================================
# Download, install, and configure Nginx as a reverse proxy
# for the Migration Automation Streamlit app.
# Run this script as Administrator.
# ============================================================

Param(
    [string]$NginxVersion = "1.27.4",
    [string]$InstallDir   = "E:\Applied Materials\Migration Web Service\nginx"
)

$ErrorActionPreference = "Stop"

# Force TLS 1.2 (required on older Windows servers)
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$zipUrl  = "https://nginx.org/download/nginx-$NginxVersion.zip"
$zipFile = "$env:TEMP\nginx-$NginxVersion.zip"

<# --- Download ---
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
#>

# --- Copy config ---
$projectConf = Join-Path $PSScriptRoot "nginx.conf"
$nginxConf   = Join-Path $InstallDir "conf\nginx.conf"

Write-Host "[*] Copying nginx.conf -> $nginxConf"
Copy-Item -Path $projectConf -Destination $nginxConf -Force

# --- Stop existing Nginx (if running) ---
$svc = Get-Service -Name "nginx" -ErrorAction SilentlyContinue
if ($svc -and $svc.Status -eq "Running") {
    Write-Host "[*] Stopping existing Nginx service ..."
    Stop-Service -Name "nginx" -Force
    Start-Sleep -Seconds 2
}
# Also kill any manual nginx processes
Get-Process -Name "nginx" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue

# --- Register as Windows Service (runs as SYSTEM) ---
$nginxExe = Join-Path $InstallDir "nginx.exe"
$serviceName = "nginx"

if (-not (Get-Service -Name $serviceName -ErrorAction SilentlyContinue)) {
    #Write-Host "[*] Installing NSSM to manage Nginx as a Windows service ..."

    <# Download NSSM (Service Manager)
    $nssmZip = "$env:TEMP\nssm.zip"
    $nssmUrl = "https://nssm.cc/release/nssm-2.24.zip"
    Invoke-WebRequest -Uri $nssmUrl -OutFile $nssmZip -UseBasicParsing
    Expand-Archive -Path $nssmZip -DestinationPath $env:TEMP -Force
    $nssmExe = Join-Path $env:TEMP "nssm-2.24\win64\nssm.exe"
    Copy-Item -Path $nssmExe -Destination $InstallDir -Force
    Remove-Item $nssmZip -Force
    #>

    $nssmPath = Join-Path $InstallDir "nssm.exe"

    Write-Host "[*] Registering Nginx as a Windows service ..."
    & $nssmPath install $serviceName $nginxExe
    & $nssmPath set $serviceName AppDirectory $InstallDir
    & $nssmPath set $serviceName Description "Nginx reverse proxy for Migration Automation"
    & $nssmPath set $serviceName Start SERVICE_AUTO_START
    Write-Host "[+] Service '$serviceName' registered (runs as Local System)" -ForegroundColor Green
} else {
    Write-Host "[=] Service '$serviceName' already exists"
}

# --- Start the service ---
Write-Host "[*] Starting Nginx service ..."
Start-Service -Name $serviceName

Start-Sleep -Seconds 2
$svc = Get-Service -Name $serviceName
if ($svc.Status -eq "Running") {
    Write-Host ""
    Write-Host "Nginx is running as a Windows service!" -ForegroundColor Green
    Write-Host "  Runs as       : Local System (not your user)"
    Write-Host "  Auto-start    : Yes (survives reboots)"
    Write-Host "  Listening on  : http://0.0.0.0:80"
    Write-Host "  Proxying to   : http://127.0.0.1:8501 (Streamlit)"
    Write-Host "  IP whitelist  : see nginx.conf geo block"
    Write-Host ""
    Write-Host "Management commands:"
    Write-Host "  Stop    : Stop-Service nginx"
    Write-Host "  Start   : Start-Service nginx"
    Write-Host "  Restart : Restart-Service nginx"
    Write-Host "  Remove  : & '$InstallDir\nssm.exe' remove nginx confirm"
} else {
    Write-Host "ERROR: Nginx service failed to start. Check $InstallDir\logs\error.log" -ForegroundColor Red
}
 
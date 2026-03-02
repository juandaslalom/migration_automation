Param(
    [string]$PythonExe = "python",
    [int]$Port = 8051
)

# Stop on errors
$ErrorActionPreference = "Stop"

Write-Host "[*] Creating virtual environment (./venv) if missing..."
if (-not (Test-Path -Path "venv")) {
    & $PythonExe -m venv venv
    Write-Host "[+] Virtual environment created."
} else {
    Write-Host "[=] Virtual environment already exists."
}

Write-Host "[*] Activating virtual environment..."
. "./venv/Scripts/Activate.ps1"

#Write-Host "[*] Installing dependencies from requirements.txt..."
#& python -m pip install --upgrade pip
#& python -m pip install -r requirements.txt
# Kill any existing Streamlit/Python processes

Write-Host "[*] Stopping existing Streamlit processes..."
Get-Process python -ErrorAction SilentlyContinue | Where-Object {
    try { $_.CommandLine -like '*streamlit*' } catch { $false }
} | ForEach-Object {
    Write-Host "    Killing PID $($_.Id)..."
    Stop-Process -Id $_.Id -Force
}
Start-Sleep -Seconds 2

Write-Host "[*] Starting Streamlit app (listening on 127.0.0.1:$Port)..."
Write-Host "    Nginx should be running on port 8050 to proxy traffic."
& streamlit run app.py --server.address 127.0.0.1 --server.port $Port --server.headless true --server.enableCORS false --server.enableXsrfProtection false --browser.gatherUsageStats false

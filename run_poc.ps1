Param(
    [string]$PythonExe = "python",
    [int]$Port = 8501
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

Write-Host "[*] Installing dependencies from requirements.txt..."
& python -m pip install --upgrade pip
& python -m pip install -r requirements.txt

Write-Host "[*] Starting Streamlit app (listening on 0.0.0.0:$Port)..."
& streamlit run app.py --server.address 0.0.0.0 --server.port $Port

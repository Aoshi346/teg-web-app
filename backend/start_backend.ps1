# Requires: PowerShell 5.1+
[CmdletBinding()]
param(
    [int]$Port = 8000
)

# Determine paths
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$VenvPath = Join-Path $ProjectRoot ".venv"
$PyPath = Join-Path $VenvPath "Scripts\python.exe"

Write-Host "Project root:" $ProjectRoot -ForegroundColor Cyan
Write-Host "Backend path:" $ScriptDir -ForegroundColor Cyan
Write-Host "Venv path:" $VenvPath -ForegroundColor Cyan

# Create venv if missing
if (-not (Test-Path $PyPath)) {
    Write-Host "Virtual environment not found. Creating at $VenvPath ..." -ForegroundColor Yellow
    $pyLauncher = Get-Command py -ErrorAction SilentlyContinue
    if ($pyLauncher) {
        & py -m venv $VenvPath
    } else {
        & python -m venv $VenvPath
    }
    if (-not (Test-Path $PyPath)) {
        Write-Error "Failed to create virtual environment. Ensure Python is installed and on PATH."
        exit 1
    }
}

# Upgrade pip and install requirements
Push-Location $ScriptDir
try {
    Write-Host "Upgrading pip..." -ForegroundColor Green
    & $PyPath -m pip install --upgrade pip

    $ReqFile = Join-Path $ScriptDir "requirements.txt"
    if (Test-Path $ReqFile) {
        Write-Host "Installing requirements from $ReqFile ..." -ForegroundColor Green
        & $PyPath -m pip install -r $ReqFile
    } else {
        Write-Warning "requirements.txt not found; installing minimal dependencies"
        & $PyPath -m pip install Django djangorestframework django-cors-headers
    }

    Write-Host "Running migrations..." -ForegroundColor Green
    & $PyPath manage.py migrate

    Write-Host "Starting Django development server on port $Port ..." -ForegroundColor Green
    & $PyPath manage.py runserver "127.0.0.1:$Port"
}
finally {
    Pop-Location
}

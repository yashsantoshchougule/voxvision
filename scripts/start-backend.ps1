$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $Python)) {
    throw "VoxVision virtual environment not found. Run: py -m venv .venv and py -m pip install -r backend\requirements.txt"
}
& $Python -m uvicorn backend.main:app --reload

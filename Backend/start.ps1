# Run GramaFix FastAPI backend with explicit app directory to avoid module resolution issues
$ErrorActionPreference = 'Stop'

# Ensure we run from the Backend folder
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

# Activate venv if you have one (optional)
# . .\.venv\Scripts\Activate.ps1

# Start the API
python -m uvicorn main:app --app-dir . --host 127.0.0.1 --port 8000
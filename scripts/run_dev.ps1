$ErrorActionPreference = "Stop"

Write-Host "Starting AI Code Review Assistant..." -ForegroundColor Green

python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
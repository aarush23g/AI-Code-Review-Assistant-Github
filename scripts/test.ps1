$ErrorActionPreference = "Stop"

Write-Host "Running tests..." -ForegroundColor Green
python -m pytest

Write-Host "Running Ruff..." -ForegroundColor Green
python -m ruff check .

Write-Host "Running Black check..." -ForegroundColor Green
python -m black --check .
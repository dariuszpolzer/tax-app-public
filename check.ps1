# tax-app local quality check
$ErrorActionPreference = "Stop"

chcp 65001 | Out-Null
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING = "utf-8"

if (-not (Test-Path ".git")) {
    Write-Host "Run this script from the tax-app repository root." -ForegroundColor Red
    exit 1
}

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "uv not found. Install uv and run again." -ForegroundColor Red
    exit 1
}

function Run-Step {
    param(
        [Parameter(Mandatory = $true)][string]$Name,
        [Parameter(Mandatory = $true)][string[]]$Command
    )

    Write-Host ""
    Write-Host "=== $Name ===" -ForegroundColor Cyan
    & $Command[0] $Command[1..($Command.Length - 1)]
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[FAIL] $Name" -ForegroundColor Red
        exit $LASTEXITCODE
    }
    Write-Host "[OK] $Name" -ForegroundColor Green
}

Write-Host "=== TAX-APP CHECK ===" -ForegroundColor Cyan
Run-Step "Python" @("uv", "run", "python", "--version")
Run-Step "Sync dependencies" @("uv", "sync", "--dev")
Run-Step "Tests" @("uv", "run", "python", "-m", "pytest")
Run-Step "Ruff" @("uv", "run", "python", "-m", "ruff", "check", ".")
Run-Step "Black" @("uv", "run", "python", "-m", "black", "--check", ".")
Run-Step "Bandit" @("uv", "run", "python", "-m", "bandit", "-q", "-c", "pyproject.toml", "-r", ".")

Write-Host ""
Write-Host "=== ALL CHECKS PASSED ===" -ForegroundColor Green

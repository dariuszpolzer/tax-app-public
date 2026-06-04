param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("AuditAll", "Doctor", "MonitorMF", "OfflineE2E", "VerifyPrevious", "SecurityCheck")]
    [string]$Action,

    [string]$TaskPath = "\TaxApp\",
    [switch]$ContinueOnError
)

$ErrorActionPreference = "Stop"

function Invoke-Step {
    param(
        [Parameter(Mandatory = $true)][string]$Name,
        [Parameter(Mandatory = $true)][scriptblock]$Command
    )

    Write-Host ""
    Write-Host "=== $Name ===" -ForegroundColor Cyan

    try {
        & $Command
        if ($LASTEXITCODE -ne 0) {
            throw "$Name failed with exit code $LASTEXITCODE"
        }
        Write-Host "[OK] $Name" -ForegroundColor Green
        return $true
    } catch {
        Write-Host "[FAIL] $Name" -ForegroundColor Red
        Write-Host $_.Exception.Message -ForegroundColor Red
        if (-not $ContinueOnError) {
            throw
        }
        return $false
    }
}

function Invoke-Doctor {
    Invoke-Step -Name "Doctor" -Command {
        & "$PSScriptRoot\check.ps1"
    }
}

function Invoke-ScheduledTaskStep {
    param([Parameter(Mandatory = $true)][string]$TaskName)

    Invoke-Step -Name $TaskName -Command {
        $fullTaskName = "$TaskPath$TaskName"
        & schtasks.exe /Run /TN $fullTaskName
    }
}

function Invoke-SecurityCheck {
    Invoke-Step -Name "security-check" -Command {
        if (Get-Command uv -ErrorAction SilentlyContinue) {
            & uv run python tools/security_check.py --redact
        } elseif (Test-Path "$PSScriptRoot\.venv\Scripts\python.exe") {
            & "$PSScriptRoot\.venv\Scripts\python.exe" tools/security_check.py --redact
        } else {
            $python = Get-Command python -ErrorAction SilentlyContinue
            if ($python) {
                & $python.Source tools/security_check.py --redact
            } else {
                & py tools/security_check.py --redact
            }
        }
    }
}

function Invoke-AuditAll {
    $results = @()
    $results += Invoke-Doctor
    $results += Invoke-ScheduledTaskStep -TaskName "MonitorMF"
    $results += Invoke-ScheduledTaskStep -TaskName "OfflineE2E"
    $results += Invoke-ScheduledTaskStep -TaskName "VerifyPrevious"
    $results += Invoke-SecurityCheck

    if ($results -contains $false) {
        Write-Host ""
        Write-Host "=== AUDITALL FAILED ===" -ForegroundColor Red
        return 1
    }

    Write-Host ""
    Write-Host "=== AUDITALL OK ===" -ForegroundColor Green
    return 0
}

switch ($Action) {
    "AuditAll" {
        exit (Invoke-AuditAll)
    }
    "Doctor" {
        $null = Invoke-Doctor
        exit 0
    }
    "MonitorMF" {
        $null = Invoke-ScheduledTaskStep -TaskName "MonitorMF"
        exit 0
    }
    "OfflineE2E" {
        $null = Invoke-ScheduledTaskStep -TaskName "OfflineE2E"
        exit 0
    }
    "VerifyPrevious" {
        $null = Invoke-ScheduledTaskStep -TaskName "VerifyPrevious"
        exit 0
    }
    "SecurityCheck" {
        $null = Invoke-SecurityCheck
        exit 0
    }
}

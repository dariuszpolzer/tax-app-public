param(
    [ValidateSet("Daily", "Weekly")]
    [string]$MonitorMFSchedule = "Daily",

    [string]$MonitorMFTime = "06:00",
    [ValidateSet("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")]
    [string]$MonitorMFWeeklyDay = "Monday",

    [Parameter(Mandatory = $true)]
    [string]$MonitorMFPath,

    [Parameter(Mandatory = $true)]
    [string]$OfflineE2EPath,

    [Parameter(Mandatory = $true)]
    [string]$VerifyPreviousPath,

    [string]$TaskPath = "\TaxApp\"
)

# Registers local tax-app orchestrator tasks in Windows Task Scheduler.
$ErrorActionPreference = "Stop"

function Resolve-TaskScriptPath {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Name
    )

    $resolved = Resolve-Path -LiteralPath $Path -ErrorAction SilentlyContinue
    if (-not $resolved) {
        throw "$Name script not found: $Path"
    }

    return $resolved.Path
}

function New-PowerShellTaskAction {
    param([Parameter(Mandatory = $true)][string]$ScriptPath)

    $arguments = "-NoProfile -ExecutionPolicy Bypass -File `"$ScriptPath`""
    return New-ScheduledTaskAction -Execute "powershell.exe" -Argument $arguments
}

function Register-OrUpdateTask {
    param(
        [Parameter(Mandatory = $true)][string]$TaskName,
        [Parameter(Mandatory = $true)]$Action,
        $Trigger,
        [string]$Description
    )

    $settings = New-ScheduledTaskSettingsSet `
        -StartWhenAvailable `
        -ExecutionTimeLimit (New-TimeSpan -Hours 3) `
        -MultipleInstances IgnoreNew

    $parameters = @{
        TaskName = $TaskName
        TaskPath = $TaskPath
        Action = $Action
        Settings = $settings
        Description = $Description
        Force = $true
    }

    if ($Trigger) {
        $parameters.Trigger = $Trigger
    }

    Register-ScheduledTask @parameters | Out-Null
}

$monitorMFScript = Resolve-TaskScriptPath -Path $MonitorMFPath -Name "MonitorMF"
$offlineE2EScript = Resolve-TaskScriptPath -Path $OfflineE2EPath -Name "OfflineE2E"
$verifyPreviousScript = Resolve-TaskScriptPath -Path $VerifyPreviousPath -Name "VerifyPrevious"

$monitorAction = New-PowerShellTaskAction -ScriptPath $monitorMFScript
if ($MonitorMFSchedule -eq "Weekly") {
    $monitorTrigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek $MonitorMFWeeklyDay -At $MonitorMFTime
} else {
    $monitorTrigger = New-ScheduledTaskTrigger -Daily -At $MonitorMFTime
}
Register-OrUpdateTask `
    -TaskName "MonitorMF" `
    -Action $monitorAction `
    -Trigger $monitorTrigger `
    -Description "Runs MonitorMF cyclically for tax-app data monitoring."

$offlineAction = New-PowerShellTaskAction -ScriptPath $offlineE2EScript
Register-OrUpdateTask `
    -TaskName "OfflineE2E" `
    -Action $offlineAction `
    -Description "On-demand OfflineE2E workflow for running after larger local changes."

$verifyAction = New-PowerShellTaskAction -ScriptPath $verifyPreviousScript
Register-OrUpdateTask `
    -TaskName "VerifyPrevious" `
    -Action $verifyAction `
    -Description "On-demand VerifyPrevious workflow for checks after month close."

Write-Host "Registered scheduled tasks:" -ForegroundColor Green
Write-Host "  $TaskPath`MonitorMF ($MonitorMFSchedule at $MonitorMFTime)"
Write-Host "  $TaskPath`OfflineE2E (on demand)"
Write-Host "  $TaskPath`VerifyPrevious (on demand)"
Write-Host ""
Write-Host "Run on-demand tasks with:"
Write-Host "  schtasks /Run /TN `"$TaskPath`OfflineE2E`""
Write-Host "  schtasks /Run /TN `"$TaskPath`VerifyPrevious`""

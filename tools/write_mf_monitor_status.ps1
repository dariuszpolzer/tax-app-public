param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("Changed", "NoChange", "Error")]
    [string]$Status,

    [Parameter(Mandatory = $true)]
    [string]$Message,

    [string]$PreviousValue = "",
    [string]$CurrentValue = "",
    [string]$SourceUrl = "",
    [string]$OutDir = ".",

    [switch]$SendMail,
    [string]$SmtpServer = "",
    [int]$SmtpPort = 587,
    [string]$MailFrom = "",
    [string]$MailTo = "",
    [switch]$UseSsl
)

# Writes the latest Ministry of Finance monitor status for reports and alerts.
$ErrorActionPreference = "Stop"

function Escape-Html {
    param([string]$Value)
    return [System.Net.WebUtility]::HtmlEncode($Value)
}

function Assert-MailConfig {
    if (-not $SmtpServer) {
        throw "SmtpServer is required when -SendMail is used."
    }
    if (-not $MailFrom) {
        throw "MailFrom is required when -SendMail is used."
    }
    if (-not $MailTo) {
        throw "MailTo is required when -SendMail is used."
    }
}

$outPath = New-Item -ItemType Directory -Force -Path $OutDir
$checkedAt = Get-Date -Format "yyyy-MM-dd HH:mm:ss zzz"

$statusTextPath = Join-Path $outPath.FullName "mf_monitor_latest_status.txt"
$statusJsonPath = Join-Path $outPath.FullName "mf_monitor_latest_status.json"
$statusHtmlPath = Join-Path $outPath.FullName "mf_monitor_alert.html"

$lines = @(
    "status=$Status",
    "checked_at=$checkedAt",
    "message=$Message"
)
if ($PreviousValue) {
    $lines += "previous=$PreviousValue"
}
if ($CurrentValue) {
    $lines += "current=$CurrentValue"
}
if ($SourceUrl) {
    $lines += "source=$SourceUrl"
}

Set-Content -LiteralPath $statusTextPath -Value $lines -Encoding UTF8

$payload = [ordered]@{
    status = $Status
    checked_at = $checkedAt
    message = $Message
    previous = $PreviousValue
    current = $CurrentValue
    source = $SourceUrl
}
$payload | ConvertTo-Json | Set-Content -LiteralPath $statusJsonPath -Encoding UTF8

$cssClass = switch ($Status) {
    "Changed" { "mf-monitor-alert changed" }
    "Error" { "mf-monitor-alert error" }
    default { "mf-monitor-alert ok" }
}

$htmlLines = @(
    "<section class=`"$cssClass`">",
    "  <h2>Monitor MF: $(Escape-Html $Status)</h2>",
    "  <p>$(Escape-Html $Message)</p>",
    "  <dl>",
    "    <dt>Sprawdzono</dt><dd>$(Escape-Html $checkedAt)</dd>"
)
if ($PreviousValue) {
    $htmlLines += "    <dt>Poprzednio</dt><dd>$(Escape-Html $PreviousValue)</dd>"
}
if ($CurrentValue) {
    $htmlLines += "    <dt>Aktualnie</dt><dd>$(Escape-Html $CurrentValue)</dd>"
}
if ($SourceUrl) {
    $escapedUrl = Escape-Html $SourceUrl
    $htmlLines += "    <dt>Zrodlo</dt><dd><a href=`"$escapedUrl`">$escapedUrl</a></dd>"
}
$htmlLines += @(
    "  </dl>",
    "</section>"
)
Set-Content -LiteralPath $statusHtmlPath -Value $htmlLines -Encoding UTF8

if ($SendMail -and $Status -ne "NoChange") {
    Assert-MailConfig

    $subject = "[tax-app] Monitor MF: $Status"
    $body = $lines -join [Environment]::NewLine
    $mailParams = @{
        SmtpServer = $SmtpServer
        Port = $SmtpPort
        From = $MailFrom
        To = $MailTo
        Subject = $subject
        Body = $body
        Encoding = "UTF8"
    }
    if ($UseSsl) {
        $mailParams.UseSsl = $true
    }

    Send-MailMessage @mailParams
}

Write-Host "Saved MF monitor status:"
Write-Host "  $statusTextPath"
Write-Host "  $statusJsonPath"
Write-Host "  $statusHtmlPath"

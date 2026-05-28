$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
uv run python tools/ftp_file_sync.py upload --file delegations_xml

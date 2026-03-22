# start_agent.ps1
# Launches the Armenian voice AI agent.
# Make sure start_livekit.ps1 is ALREADY running in another terminal.

Set-Location -Path $PSScriptRoot

Write-Host "Starting Armenian Voice AI Agent..." -ForegroundColor Green
Write-Host "Make sure LiveKit is running (start_livekit.ps1) first!" -ForegroundColor Yellow
Write-Host ""

python main.py dev

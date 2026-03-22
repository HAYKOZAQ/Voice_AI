# start_livekit.ps1
# Launches the local LiveKit server in development mode.
# Run this FIRST in a separate terminal before starting the agent.
# Dev mode uses: API key = "devkey", API secret = "secret", port = 7880

$LIVEKIT_EXE = "D:\DATA\livekit-server\livekit-server.exe"

if (-not (Test-Path $LIVEKIT_EXE)) {
    Write-Error "LiveKit server binary not found at: $LIVEKIT_EXE"
    exit 1
}

Write-Host "Starting LiveKit server in dev mode on ws://localhost:7880" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop." -ForegroundColor Yellow
Write-Host ""

& $LIVEKIT_EXE --dev

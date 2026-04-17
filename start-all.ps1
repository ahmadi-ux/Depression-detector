# Start all three services: Ollama, API, and Frontend
# Run with .\start-all.ps1

$line = "================================================================================"

Write-Host $line -ForegroundColor Cyan
Write-Host "Starting Depression Detector - All Services" -ForegroundColor Green
Write-Host $line -ForegroundColor Cyan
Write-Host ""

# Get the project root directory
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

# Start Ollama in a new terminal
Write-Host "Starting Ollama server..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "ollama serve" -WindowStyle Normal

# Wait a moment for Ollama to start
Start-Sleep -Seconds 3

# Start API in a new terminal
Write-Host "Starting API server..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$projectRoot'; python .\api\app.py" -WindowStyle Normal

# Wait a moment for API to start
Start-Sleep -Seconds 3

# Start Frontend in a new terminal
Write-Host "Starting Frontend (Vite)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$projectRoot\vite-project'; npm run dev" -WindowStyle Normal

Write-Host ""
Write-Host $line -ForegroundColor Cyan
Write-Host "All services started!" -ForegroundColor Green
Write-Host "Services should be running at:" -ForegroundColor Cyan
Write-Host "  Ollama:   http://localhost:11434" -ForegroundColor White
Write-Host "  API:      http://localhost:5000" -ForegroundColor White
Write-Host "  Frontend: http://localhost:5173" -ForegroundColor White
Write-Host $line -ForegroundColor Cyan
